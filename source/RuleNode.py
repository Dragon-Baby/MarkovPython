from re import search
from xmlrpc.client import FastMarshaller
from Node import Node
from Rule import Rule
from Field import Field
from Observation import Observation
import Search
from abc import ABC, abstractmethod
import XMLHelper as XH
import SymmetryHelper as SH
from AllNode import AllNode


class RuleNode(Node, ABC):
    def __init__(self):
        super().__init__()
        self.rules = []
        self.counter = 0
        self.steps = 0

        self.matches = []
        self.match_count = 0
        self.last_matched_turn = 0
        self.match_mask = [[]]
        
        self.potentials = [[]]
        self.fields = []
        self.observations = []
        self.temperature = 0.0

        self.search = False
        self.future_computed = False
        self.future = []
        self.trajectory = []

        self.limit = 0
        self.depth_coefficient = 0.0

        self.last = []

    def Load(self, xelem, parent_symmetry, grid):
        symmetry_str = XH.GetValue(xelem, "symmetry", "")
        symmetry = SH.GetSymmetry(grid.MZ==1, symmetry_str, parent_symmetry)
        if symmetry == []:
            print("unknown symmetry {0} at line {1}".format(symmetry_str, xelem._start_line_number))
            return False
        
        rule_list = []
        xrules = XH.Elements(xelem, ["rule"])
        rule_elements = xrules if len(xrules) > 0 else [xelem]
        for xrule in rule_elements:
            rule = Rule.Load(xrule, grid, grid)
            if rule == None:
                return False
            rule.original = True

            rule_symmetry_str = XH.GetValue(xrule, "symmetry", "")
            rule_symmetry = SH.GetSymmetry(grid.MZ == 1, rule_symmetry_str, symmetry)
            if rule_symmetry == []:
                print("unknown symmetry {0} at line {1}".format(rule_symmetry_str, xrule._start_line_number))
                return False
            for r in rule.Symmetries(rule_symmetry, grid.MZ == 1):
                rule_list.append(r)

        rules = rule_list
        self.last = [False] * len(rules)

        # field
        self.steps = XH.GetValue(xelem, "temperature", 0.0)
        xfields = XH.Elements(xelem, ["field"])
        if len(xfields) != 0:
            fields = [None] * grid.C
            for xfield in xfields:
                c = XH.GetValue(xfield, "for", "")
                if c in grid.values.keys():
                    value = grid.values[c]
                    fields[value] = Field(xfield, grid)
                else:
                    print("unknown field value {0} at line {1}".format(c, xfield._start_line_number))
            self.potentials = [[0]*len(grid.state)]*len(grid.C)

        # observe
        xobservations = XH.Elements(xelem, ["observe"])
        if len(xobservations) != 0:
            observations = [None]*grid.C
            for x in xobservations:
                value = grid.values[XH.GetValue(x, "value", "")]
                observations[value] = Observation(XH.GetValue(x, "from", grid.characters[value]), XH.GetValue(x, "to", ""), grid)

            search = XH.GetValue(xelem, "search", False)
            if search:
                self.limit = XH.GetValue(xelem, "limit", -1)
                self.depth_coefficient = XH.GetValue(xelem, "depthCoefficient", 0.5)
            else:
                self.potentials = [[0]*len(grid.state)]*len(grid.C)
            self.future = [0]*len(grid.state)

        return True

    def Reset(self):
        self.last_matched_turn = -1
        self.counter = 0
        self.future_computed = False
        for r in range(len(self.last)):
            self.last[r] = False

    
    @abstractmethod
    def Add(self, r, x, y, z, maskr):
        maskr[x + y * self.grid.MX + z * self.grid.MX * self.grid.MY] = True

        match = (r, x, y, z)
        if self.match_count < len(self.matches):
            self.matches[self.match_count] = match
        else:
            self.matches.append(match)
        self.match_count += 1

    def Go(self):
        for r in range(len(self.last)):
            self.last[r] = False
        if self.steps > 0 and self.counter >= self.steps:
            return False
        MX = self.grid.MX
        MY = self.grid.MY
        MZ = self.grid.MZ
        if self.observations != [] and not self.future_computed:
            if not Observation.ComputeFutureSetPresent(self.future, self.grid.state, self.observations):
                return False
            else:
                self.future_computed = True
                if search:
                    self.trajectory = []
                    TRIES = 1 if self.limit < 0 else 20
                    k = 0
                    while k < TRIES and self.trajectory == []:
                        self.trajectory = Search.Run(self.grid.state, self.future, self.rules, self.grid.MX, self.grid.MY, self.grid.MZ, self.grid.C, type(self) is AllNode, self.limit, self.depthCoefficient, self.ip.random)
                        k += 1
                    if self.trajectory == []:
                        print("SEARCH RETURNED NULL")
                else:
                    Observation.ComputeBackwardPotentials(self.potentials, self.future, MX, MY, MZ, self.rules)
        
        if self.last_matched_turn >= 0:
            for n in range(self.ip.first[self.last_matched_turn], len(self.ip.changes)):
                (x,y,z) = self.ip.changes[n]
                value = self.grid.state[x + y * MX + z * MX * MY]
                for r in range(len(self.rules)):
                    rule = self.rules[r]
                    maskr = self.match_mask[r]
                    shifts = rule.ishift[value]
                    for l in range(len(shifts)):
                        (shiftx, shifty, shiftz) = shifts[l]
                        sx = x - shiftx
                        sy = y - shifty
                        sz = z - shiftz

                        if sx < 0 or sy < 0 or sz < 0 or sx + rule.IMX > MX or sy + rule.IMY > MY or sz + rule.IMZ > MZ:
                            continue
                        si = sx + sy * MX + sz * MX * MY
                        if not maskr[si] and self.grid.Matches(rule, sx, sy, sz):
                            self.Add(r, sx, sy, sz, maskr)

        else:
            match_count = 0
            for r in range(len(self.rules)):
                rule = self.rule[r]
                maskr = self.match_mask[r]
                for z in range(rule.IMZ - 1, MZ, rule.IMZ):
                    for y in range(rule.IMY - 1, MY, rule.IMY):
                        for x in range(rule.IMX - 1, MX, rule.IMX):
                            shifts = rule.ishifts[self.grid.state[x + y * MX + z * MX * MY]]
                            for l in range(len(shifts)):
                                (shiftx, shifty, shiftz) = shifts[l]
                                sx = x - shiftx
                                sy = y - shifty
                                sz = z - shiftz
                                if sx < 0 or sy < 0 or sz < 0 or sx + rule.IMX > MX or sy + rule.IMY > MY or sz + rule.IMZ > MZ:
                                    continue
                                if self.grid.Matches(rule, sx, sy, sz):
                                    self.Add(r, sx, sy, sz, maskr)

        if self.fields != []:
            anysuccess = anycomputation = False
            for c in range(len(self.fields)):
                field = self.fields[c]
                if field != None and (self.counter == 0 or field.recompute):
                    success = field.Compute(self.potentials[c], self.grid)
                    if not success and field.essential:
                        return False
                    anysuccess = anysuccess | success
                    anycomputation = True
            if anycomputation and not anysuccess:
                return False
        
        return True

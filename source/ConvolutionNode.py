from source import XMLHelper as XH
from source import Node
import random as rd
import sys

class ConvolutionNode(Node):
    def __init__(self):
        super().__init__()
        self.rules = []
        self.kernel = []
        # periodic 周期
        self.periodic = False
        self.counter = self.steps = 0

        self.sumfield = [[]]
        
        self.kernels2d = {
            "VonNeumann" : [0, 1, 0, 1, 0, 1, 0, 1, 0],
            "Moore" : [1, 1, 1, 1, 0, 1, 1, 1, 1]
        }

        self.kernels3d = {
            "VonNeumann" : [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            "NoCorners" : [0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0]
        }

    def Load(self, xelem, parent_symmetry, grid):
        xrules = XH.Elements(xelem, ["rule"])
        if len(xrules) == 0:
            xrules = [xelem]
        self.rules = [None] * len(xrules)
        for k in range(len(self.rules)):
            self.rules[k] = ConvolutionRule()
            if not self.rules[k].Load(xrules[k], grid):
                return False
        
        self.steps = XH.GetValue(xelem, "steps", -1)
        self.periodic = XH.GetValue(xelem, "periodic", False)
        neighborhood = XH.GetValue(xelem, "neighborhood", "")
        self.kernel = self.kernels2d[neighborhood] if grid.MZ == 1 else self.kernels3d[neighborhood]

        self.sumfield = [[0]*grid.C] * len(grid.state)
        return True

    def Reset(self):
        self.counter = 0

    def Go(self):
        if self.steps > 0 and self.counter >= self.steps:
            return False
        MX = self.grid.MX
        MY = self.grid.MY
        MZ = self.grid.MZ

        for sf in self.sumfield:
            for s in sf:
                s = 0

        if MZ == 1:
            for y in range(MY):
                for x in range(MX):
                    sums = self.sumfield[x + y * MX]
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            sx = x + dx
                            sy = y + dy

                            if self.periodic:
                                if sx < 0:
                                    sx += MX
                                elif sx >= MX:
                                    sx -= MX
                                if sy < 0:
                                    sy += MY
                                elif sy >= MY:
                                    sy -= MY
                            elif sx < 0 or sy < 0 or sx >= MX or sy >= MY:
                                continue
                            sums[self.grid.state[sx + sy * MX]] += self.kernel[dx + 1 + (dy + 1) * 3]
        else:
            for z in range(MZ):
                for y in range(MY):
                    for x in range(MX):
                        sums = self.sumfield[x + y * MX + z * MX * MY]
                        for dz in range(-1, 2):
                            for dy in range(-1, 2):
                                for dx in range(-1, 2):
                                    sx = x + dx
                                    sy = y + dy
                                    sz = z + dz

                                    if self.periodic:
                                        if sx < 0:
                                            sx += MX
                                        elif sx >= MX:
                                            sx -= MX
                                        if sy < 0:
                                            sy += MY
                                        elif sy >= MY:
                                            sy -= MY
                                        if sz < 0:
                                            sz += MZ
                                        elif sz >= MZ:
                                            sz -= MZ
                                    elif sx < 0 or sy < 0 or sz < 0 or sx >= MX or sy >= MY or sz >= MZ:
                                        continue
                                    sums[self.grid.state[sx + sy * MX + sz * MX * MY]] += self.kernel[dx + 1 + (dy + 1) * 3 + (dz + 1) * 9]

        change = False
        for i in range(len(self.sumfield)):
            sums = self.sumfield[i]
            input = self.grid.state[i]
            for r in range(len(self.rules)):
                rule = self.rules[r]
                rd.seed(self.ip.random)
                if input == rule.input and rule.output != self.grid.state[i] and (rule.p == 1.0 or rd.randrange(0, sys.maxsize) < rule.p * sys.maxsize):
                    success = True
                    if rule.sums != []:
                        sum = 0
                        for c in range(len(rule.values)):
                            sum += sums[rule.values[c]]
                        success = rule.sums[sum]
                    if success:
                        self.grid.state[i] = rule.output
                        change = True
                        break

        self.counter += 1
        return change

class ConvolutionRule():
    def __init__(self):
        self.input = self.output = 0
        self.values = []
        self.sums = []
        self.p = 0.0

    def Load(self, xelem, grid):
        self.input = grid.values[XH.GetValue(xelem, "in", "")]
        self.output = grid.values[XH.GetValue(xelem, "out", "")]
        self.p = XH.GetValue(xelem, "p", 1.0)

        def interval(s):
            if "." in s:
                bounds = s.split("..")
                min = int(bounds[0])
                max = int(bounds[1])
                result = [0]*(max - min + 1)
                for i in range(len(result)):
                    result[i] = min + i
                return result
            else:
                return [int(s)]

        value_str = XH.GetValue(xelem, "values", "")
        sums_str = XH.GetValue(xelem, "sum", "")
        if value_str != "" and sums_str == "":
            print("missing \"sum\" attribute at line {0}".format(xelem._start_line_number))
            return False
        if value_str == "" and sums_str != "":
            print("missing \"values\" attribute at line {0}".format(xelem._start_line_number))
            return False
        if value_str != "":
            self.values = list(map(lambda c : grid.values[c], list(value_str)))

            self.sums = [False] * 28
            intervals = sums_str.split(",")
            for s in intervals:
                for i in interval(s):
                    self.sums[i] = True
        return True
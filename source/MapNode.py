import XMLHelper as XH
from Node import Node, Branch
from Rule import Rule
from Grid import Grid
import SymmetryHelper as SH

class MapNode(Branch):
    def __init__(self):
        super().__init__()
        self.new_grid = None
        self.rules = []
        self.NX = self.NY = self.NZ = self.DX = self.DY = self.DZ = 0

    def Load(self, xelem, parent_symmetry, grid):
        scale_str = XH.GetValue(xelem, "scale", "")
        if scale_str == "":
            print("scale should be specified in map node")
            return False
        scales = scale_str.split(' ')
        if len(scales) != 3:
            print("scale attribute \"{0}\" should have 3 components separated by space")
            return False

        def readScale(s):
            if not "/" in s:
                return (int(s), 1)
            else:
                nd = s.split("/")
                return (int(nd[0]), int(nd[1]))
        
        (NX, DX) = readScale(scales[0])
        (NY, DY) = readScale(scales[1])
        (NZ, DZ) = readScale(scales[2])

        self.new_grid = Grid.Load(xelem, grid.MX * NX / DX, grid.MY * NY / DY, grid.MZ * NZ / DZ)
        if self.new_grid == None:
            return False
        
        if not super().Load(xelem, parent_symmetry, self.new_grid):
            return False
        symmetry = SH.GetSymmetry(grid.MZ == 1, XH.GetValue(xelem, "symmetry", ""), parent_symmetry)

        rule_list = []
        for xrule in XH.Elements(xelem, ["rule"]):
            rule = Rule.Load(xrule, grid, self.new_grid)
            rule.original = True
            if rule == None:
                return False
            for r in rule.Symmetries(symmetry, grid.MZ == 1):
                rule_list.append(r)

        self.rules = rule_list
        return True

    @staticmethod
    def Matches(rule, x, y, z, state, MX, MY, MZ):
        for dz in range(rule.IMZ):
            for dy in range(rule.IMY):
                for dx in range(rule.IMX):
                    sx = x + dx
                    sy = y + dy
                    sz = z + dz

                    if sx >= MX:
                        sx -= MX
                    if sy >= MY:
                        sy -= MY
                    if sz >= MZ:
                        sz -= MZ
                    
                    input_wave = rule.input[dx + dy * rule.IMX + dz * rule.IMX * rule.IMY]
                    if (input_wave & (1 << state[sx + sy * MX + sz * MX * MY])) == 0:
                        return False
        return True


    @staticmethod
    def Apply(rule, x, y, z, state, MX, MY, MZ):
        for dz in range(rule.OMZ):
            for dy in range(rule.OMY):
                for dx in range(rule.OMX):
                    sx = x + dx
                    sy = y + dy
                    sz = z + dz

                    if sx >= MX:
                        sx -= MX
                    if sy >= MY:
                        sy -= MY
                    if sz >= MZ:
                        sz -= MZ
                    
                    output = rule.output[dx + dy * rule.OMX + dz * rule.OMX * rule.OMY]
                    if output != 0xff:
                        state[sx + sy * MX + sz * MX * MY]
                        

    def Go(self):
        if self.n >= 0:
            super().Go()
        self.new_grid.Clear()
        for rule in self.rules:
            for z in range(self.grid.MZ):
                for y in range(self.grid.MY):
                    for x in range(self.grid.MX):
                        if MapNode.Matches(rule, x, y, z, self.grid.state, self.grid.MX, self.grid.MY, self.grid.MZ):
                            MapNode.Apply(rule, x * self.NX / self.DX, y * self.NY / self.DY, z * self.NZ / self.DZ, self.new_grid.state, self.new_grid.MX, self.new_grid.MY, self.new_grid.MZ)
        self.ip.grid = self.new_grid
        self.n += 1
        return True

    def Reset(self):
        super().Reset()
        self.n = -1
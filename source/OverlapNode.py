import XMLHelper as XH
import WFCNode
import SymmetryHelper as SH
import Graphics 
import Helper as He
import random as rd

class OverlapNode(WFCNode.WFCNode):
    def __init__(self):
        super().__init__()
        self.patterns = [[]]

    def Load(self, xelem, parent_symmetry, grid):
        import Grid
        if grid.Z != 1:
            print("overlapping model currently works only for 2d")
            return False
        self.N = XH.GetValue(xelem, "n", 3)

        symmetry_str = XH.GetValue(xelem, "symmetry", "")
        symmetry = SH.GetSymmetry(True, symmetry_str, parent_symmetry)
        if symmetry == []:
            print("unknown symmetry {0} at line {1}".format(symmetry_str, xelem._start_line_number))
            return False
        
        periodic_input = XH.GetValue(xelem, "periodicInput", False)

        self.new_grid = Grid.Grid.Load(xelem, grid.MX, grid.MY, grid.MZ)
        if self.new_grid != None:
            return False
        self.periodic = True

        self.name = XH.GetValue(xelem, "sample", "")
        (bitmap, SMX, SMY, _) = Graphics.LoadBitmap("resources/samples/{0}.png".format(self.name))
        if bitmap == []:
            print("couldn't read sample {0}".format(self.name))
            return False
        (sample, C) = He.Ords(bitmap)
        if C > self.new_grid.C:
            print("there were more than {0} colors in the sample".format(self.new_grid.C))
            return False
        W = He.Power(C, self.N * self.N)

        def patternFromIndex(ind):
            # residue 残余
            residue = ind
            power = W
            result = [0] * self.N * self.N
            for i in range(len(result)):
                power /= C
                count = 0
                while residue >= power:
                    residue -= power
                    count += 1
                result[i] = count
            return result

        weights = {}
        ordering = []

        ymax = grid.MY if periodic_input else grid.MY - self.N + 1
        xmax = grid.MX if periodic_input else grid.MX - self.N + 1
        for y in range(ymax):
            for x in range(xmax):
                pattern = He.Pattern(lambda dx, dy : sample[(x + dx) % SMX + ((y + dy) % SMY) * SMX], self.N)
                symmetries = SH.SquareSymmetries(pattern, lambda q : He.Rotated(q, self.N), lambda q : He.Reflected(q, self.N), lambda q1, q2 : False, symmetry)
                for p in symmetries:
                    ind = He.IndexByteArray(C)
                    if ind in weights.keys():
                        weights[ind] += 1
                    else:
                        weights[ind] = 1
                        ordering.append(ind)

        self.P = len(weights)
        print("number of patterns P = {0}".format(self.P))

        self.patterns = [[]] * self.P
        super().weights = [0.0] * self.P
        counter = 0
        for w in ordering:
            self.patterns[counter] = patternFromIndex(w)
            super().weights[counter] = weights[w]
            counter += 1

        def agrees(p1, p2, dx, dy):
            xmin = 0 if dx < 0 else dx
            xmax = dx + self.N if dx < 0 else self.N
            ymin = 0 if dy < 0 else dy
            ymax = dy + self.N if dy < 0 else self.N
            for y in range(ymin, ymax):
                for x in range(xmin, xmax):
                    if p1[x + self.N * y] != p2[x - dx + self.N * (y - dy)]:
                        return False
            return True

        self.propagator = [[[]]]*4
        for d in range(4):
            self.propagator[d] = [[]] * self.P
            for t in range(self.P):
                list = []
                for t2 in range(self.P):
                    if agrees(self.patterns[t], self.patterns[t2], self.DX[d], self.DY[d]):
                        list.append(t2)
                self.propagator[d][t] = [0] * len(list)
                for c in range(len(list)):
                    self.propagator[d][t][c] = list[c]

        map = {}
        for xrule in XH.Elements(xelem, ["rule"]):
            input = XH.GetValue(xelem, "in", "")
            outputs = list(map(lambda s : self.new_grid.values[s[0]], XH.GetValue(xelem, "out", "").split("|")))
            position = list(map(lambda t : self.patterns[t][0] in outputs.keys(), list(range(0, self.P))))
            map[grid.values[input]] = position
        
        if not 0 in map.keys():
            map[0] = [True] * self.P

        return super().Load(xelem, parent_symmetry, grid)


    def UpdateState(self):
        MX = self.new_grid.MX
        MY = self.new_grid.MY
        votes = [[0]*self.new_grid.C] * len(self.new_grid.state)
        for i in range(len(self.wave.data)):
            w = self.wave.data[i]
            x = int(i % MX)
            y = int(i / MX)
            for p in range(self.P):
                if w[p]:
                    pattern = self.patterns[p]
                    for dy in range(self.N):
                        ydy = y + dy
                        if ydy >= MY:
                            ydy -= MY
                        for dx in range(self.N):
                            xdx = x + dx
                            if xdx >= MX:
                                xdx -= MX
                            value = pattern[dx + dy * self.N]
                            votes[xdx + ydy * MX][value] += 1

        for i in range(len(votes)):
            max = -1.0
            argmax = 0xff
            v = votes[i]
            for c in range(len(v)):
                value = v[c] + 0.1 * rd.random()
                if value > max:
                    argmax = c
                    max = value
            self.new_grid.state[i] = argmax
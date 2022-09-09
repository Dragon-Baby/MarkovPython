import RuleNode
import random as rd
import math
import Helper as He


class AllNode(RuleNode.RuleNode):
    def __init__(self):
        super().__init__()   

    def Load(self, xelem, parent_symmetry, grid):
        if not super().Load(xelem, parent_symmetry, grid):
            return False
        self.matches = []
        self.match_mask = [[False]*(len(grid.state))]*len(self.rules)
        return True

    def Fit(self, r, x, y, z, new_state, MX, MY):
        rule = self.rules[r]
        for dz in range(rule.OMZ):
            for dy in range(rule.OMY):
                for dx in range(rule.OMX):
                    value = rule.ouput[dx + dy * rule.OMX + dz * rule.OMX * rule.OMY]
                    if value != 0xff and new_state[x + dx + (y + dy) * MX + (z + dz) * MX * MY]:
                        return
        self.last[r] = True
        for dz in range(rule.OMZ):
            for dy in range(rule.OMY):
                for dx in range(rule.OMX):
                    newvalue = rule.output[dx + dy * rule.OMX + dz * rule.OMX * rule.OMY]
                    if newvalue != 0xff:
                        sx = x + dx
                        sy = y + dy
                        sz = z + dz
                        i = sx + sy * MX + sz * MX * MY
                        new_state[i] = True
                        self.grid.state[i] = newvalue
                        self.ip.changes.append((sx,sy,sz))

    def Go(self):
        print("Go for Node:{0}".format(self))
        if not super().Go():
            return False
        self.last_matched_turn = self.ip.counter

        if self.trajectory != []:
            if self.counter >= len(self.trajectory):
                return False
            self.grid.state = self.trajectory[self.counter][:len(self.grid.state)]
            self.counter += 1
            return True

        if self.match_count == 0:
            return False

        MX = self.grid.MX
        MY = self.grid.MY
        import Field
        if self.potentials != []:
            first_heuristic = 0
            first_heuristic_computed = False
            list = []
            for m in range(self.match_count):
                (r, x, y, z) = self.matches[m]
                heuristic = Field.DeltaPointwise(self.grid.state, self.rules[r], x, y, z, self.fields, self.potentials, self.grid.MX, self.grid.MY)
                if heuristic != None:
                    h = float(heuristic)
                    if not first_heuristic_computed:
                        first_heuristic = h
                        first_heuristic_computed = True
                    u = rd.uniform(0,1)
                    list.append((m, math.pow(u, math.exp((h - first_heuristic) / self.temperature)) if self.temperature > 0 else -h + 0.001 * u))
            ordered = sorted(list, key=lambda x : -x[1])
            for k in range(len(ordered)):
                (r,x,y,z) = self.matches[ordered[k][0]]
                self.match_mask[r][x + y * MX + z * MX * MY] = False
                self.Fit(r, x, y, z, self.grid.mask, MX, MY)
        else:
            shuffle = [0]*self.match_count
            He.Shuffle(shuffle, self.ip.random)
            for k in range(len(shuffle)):
                (r,x,y,z) = self.matches[shuffle[k]]
                self.match_mask[r][x + y * MX + z * MX * MY] = False
                self.Fit(r, x, y, z, self.grid.mask, MX, MY)

        for n in range(self.ip.first[self.last_matched_turn], len(self.ip.changes)):
            (x,y,z) = self.ip.changes[n]
            self.grid.mask[x + y * MX + z * MX * MY] = False

        self.counter += 1
        self.match_count = 0
        return True
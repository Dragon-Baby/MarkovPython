import random as rd
import math
import RuleNode


class OneNode(RuleNode.RuleNode):
    def __init__(self):
        super().__init__()

    def Load(self, xelem, parent_symmetry, grid):
        if not super().Load(xelem, parent_symmetry, grid):
            print("failed to load as rule node!")
            return False
        self.matches = []
        self.match_mask = [[False]*len(grid.state)]*len(self.rules)
        print("successed to load as one node!")
        return True

    def Reset(self):
        super().Reset()
        if self.match_count != 0:
            for mm in self.match_mask:
                for m in mm:
                    m = False
            self.match_count = 0

    def Apply(self, rule, x, y, z):
        MX = self.grid.MX
        MY = self.grid.MY
        changes = self.ip.changes
        for dz in range(rule.OMZ):
            for dy in range(rule.OMY):
                for dx in range(rule.OMX):
                    new_value = rule.output[dx + dy * rule.OMX + dz * rule.OMX * rule.OMY]
                    if new_value != 0xff:
                        sx = x + dx
                        sy = y + dy
                        sz = z + dz
                        si = sx + sy * MX + sz * MX * MY
                        old_value = self.grid.state[si]
                        if new_value != old_value:
                            self.grid.state[si] = new_value
                            changes.append((sx,sy,sz))
    
    def Go(self):
        print("Go for Node:{0}".format(self))
        if not super().Go():
            print("Failed to Go as a Rule node!")
            return False
        self.last_matched_turn = self.ip.counter

        if self.trajectory != []:
            if self.counter >= len(self.trajectory):
                return False
            self.grid.state = self.trajectory[self.counter][:len(self.grid.state)]
            self.counter += 1
            return True
        
        R, X, Y, Z = self.RandomMatch(self.ip.random)
        if R < 0:
            print("Failed！")
            return False
        else:
            self.last[R] = True
            self.Apply(self.rules[R], X, Y, Z)
            self.counter += 1
            print("Worked!")
            return True

    def RandomMatch(self, random):
        print("Start RandomMatch!")
        import Observation
        import Field
        if self.potentials != []:
            print("There're exist potential!")
            if self.observations != [] and Observation.Observation.IsGoalReached(self.grid.state, self.future):
                self.future_computed = False
                return (-1,-1,-1,-1)
            max = -1000.0
            argmax = -1
            # heuristic 探索
            first_heuristic = 0.0
            first_heuristic_computed = False
            k = 0
            while k < self.match_count:
                (r,x,y,z) = self.matches[k]
                i = x + y * self.grid.MX + z * self.grid.MX * self.grid.MY
                if not self.grid.Matches(self.rules[r], x, y, z):
                    self.match_mask[r][i] = False
                    self.matches[k] = self.matches[self.match_count - 1]
                    self.match_count -= 1
                    k -= 1
                else:
                    heuristic = Field.Field.DeltaPointwise(self.grid.state, self.rules[r], x, y, z, self.fields, self.potentials, self.grid.MX, self.grid.MY)
                    if heuristic == None:
                        continue
                    h = float(heuristic)
                    if not first_heuristic_computed:
                        first_heuristic = h
                        first_heuristic_computed = True
                    u = rd.uniform(0,1)
                    key = math.pow(u, math.exp((h - first_heuristic) / self.temperature)) if self.temperature > 0 else -h + 0.001 * u
                    if key > max:
                        max = key
                        argmax = k
                k += 1
            return self.matches[argmax] if argmax >= 0 else (-1,-1,-1,-1)
        else:
            print("match_count:{0}".format(self.match_count))
            while self.match_count > 0:
                rd.seed(self.ip.random)
                match_index = rd.randrange(0, self.match_count)
                (r, x, y, z) = self.matches[match_index]
                i = x + y * self.grid.MX + z * self.grid.MX * self.grid.MY

                self.match_mask[r][i] = False
                self.matches[match_index] = self.matches[self.match_count - 1]
                self.match_count -= 1

                if self.grid.Matches(self.rules[r], x, y, z):
                    return (r, x, y, z)
            return (-1,-1,-1,-1)
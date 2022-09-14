import random as rd
import math
import RuleNode


class OneNode(RuleNode.RuleNode):
    def __init__(self):
        print("[OneNode] > Factory a OneNode")
        super().__init__()


    def Load(self, xelem, parent_symmetry, grid):
        print("[OneNode] > Load for OneNode at line {0}!".format(self.start_line))
        print("[OneNode] > Load as a RuleNode!")
        if not super().Load(xelem, parent_symmetry, grid):
            print("[OneNode] > !!! Failed to Load as a OneNode !!!")
            return False
        self.matches = []
        self.match_mask = [[False for i in range(len(grid.state))] for i in range(len(self.rules))]
        return True


    def Reset(self):
        super().Reset()
        if self.match_count != 0:
            for mm in self.match_mask:
                mm = [False for i in range(len(mm))]
            self.match_count = 0


    def Apply(self, rule, x, y, z):
        MX = self.grid.MX
        MY = self.grid.MY
        changes = self.ip.changes

        for dz in range(rule.OMZ):
            for dy in range(rule.OMY):
                for dx in range(rule.OMX):
                    # byte
                    new_value = rule.output[dx + dy * rule.OMX + dz * rule.OMX * rule.OMY]
                    if new_value != 0xff:
                        sx = x + dx
                        sy = y + dy
                        sz = z + dz
                        si = sx + sy * MX + sz * MX * MY
                        # byte
                        old_value = self.grid.state[si]
                        if new_value != old_value:
                            self.grid.state[si] = new_value
                            changes.append((sx,sy,sz))
    
    def Go(self):
        if not super().Go():
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
            return False
        else:
            self.last[R] = True
            self.Apply(self.rules[R], X, Y, Z)
            self.counter += 1
            return True

    # return int, int, int, int 
    def RandomMatch(self, random):
        import Observation
        import Field

        if self.potentials != []:
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
            
            while self.match_count > 0:
                match_index = rd.randrange(0, self.match_count)
                (r, x, y, z) = self.matches[match_index]
                i = x + y * self.grid.MX + z * self.grid.MX * self.grid.MY

                self.match_mask[r][i] = False
                self.matches[match_index] = self.matches[self.match_count - 1]
                self.match_count -= 1

                if self.grid.Matches(self.rules[r], x, y, z):
                    return (r, x, y, z)
            return (-1,-1,-1,-1)
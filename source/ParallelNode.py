import RuleNode
import random as rd

class ParallelNode(RuleNode.RuleNode):
    def __init__(self):
        super().__init__()
        self.new_state = []

    def Load(self, xelem, parent_symmetry, grid):
        print("Now is Parallel!")
        if not super().Load(xelem, parent_symmetry, grid):
            print("Parallel Failed!")
            return False
        self.new_state = [0] * len(grid.state)
        return True

    def Add(self, r, x, y, z, maskr):
        rule = self.rules[r]
        if rd.uniform(0,1) > rule.p:
            return
        self.last[r] = True
        MX = self.grid.MX
        MY = self.grid.MY

        for dz in range(rule.OMZ):
            for dy in range(rule.OMY):
                for dx in range(rule.OMX):
                    newvalue = rule.output[dx + dy * rule.OMX + dz * rule.OMX * rule.OMY]
                    idi = x + dx + (y + dy) * MX + (z + dz) * MX * MY
                    if newvalue != 0xff and newvalue != self.grid.state[idi]:
                        self.newstate[idi] = newvalue
                        self.ip.changes.append((x + dx, y + dy, z + dz))
        self.match_count += 1

    def Go(self):
        print("Go for Node:{0}".format(self))
        if not super().Go():
            return False
        for n in range(self.ip.first[self.ip.counter], len(self.ip.changes)):
            (x,y,z) = self.ip.changes[n]
            i = x + y * self.grid.MX + z * self.grid.MX * self.grid.MY
            self.grid.state[i] = self.new_state[i]
        self.counter += 1
        return self.match_count > 0
class Observation():
    def __init__(self, f, t, grid):
        self.fro = grid.values[f]
        self.to = grid.Wave(t)

    @staticmethod
    def ComputeFutureSetPresent(future, state, observations):
        mask = [False] * len(observations)
        for k in range(len(observations)):
            if observations[k] == None:
                mask[k] = True
        for i in range(len(state)):
            value = state[i]
            obs = observations[value]
            mask[value] = True
            if obs != None:
                future[i] = obs.to
                state[i] = obs.fro
            else:
                future[i] = 1 << value

        for k in range(len(mask)):
            if not mask[k]:
                return False

        return True

    @staticmethod
    def ComputeForwardPotentials(potentials, state, MX, MY, MZ, rules):
        for pot in potentials:
            for p in pot:
                p = -1
        for i in range(len(state)):
            potentials[state[i]][i] = 0
        Observation.ComputePotentials(potentials, MX, MY, MZ, rules, False)

    @staticmethod
    def ComputeBackwardPotentials(potentials, future, MX, MY, MZ, rules):
        for c in range(len(potentials)):
            potential = potentials[c]
            for i in range(len(future)):
                potential[i] = 0 if (future[i] & (1 << c)) != 0 else -1
        Observation.ComputePotentials(potentials, MX, MY, MZ, rules, True)

    @staticmethod
    def ComputePotentials(potentials, MX, MY, MZ, rules, backwards):
        queue = []
        for c in range(len(potentials)):
            potential = potentials[c]
            for i in range(len(potential)):
                if potential[i] == 0:
                    queue.append((c, i % MX, (i % (MX * MY)) / MX, i / (MX * MY)))
        match_mask = [[False]*len(potentials[0])] * len(rules)

        while len(queue) != 0:
            (value, x, y, z) = queue.pop(0)
            i = x + y * MX + z * MX * MY
            t = potentials[value][i]
            for r in range(len(rules)):
                maskr = match_mask[r]
                rule = rules[r]
                shifts = rule.oshifts[value] if backwards else rule.ishifts[value]
                for l in range(len(shifts)):
                    (shiftx, shifty, shiftz) = shifts[l]
                    sx = x - shiftx
                    sy = y - shifty
                    sz = z - shiftz

                    if sx < 0 or sy < 0 or sz < 0 or sx + rule.IMX > MX or sy + rule.IMY > MY or sz + rule.IMZ > MZ:
                        continue
                    si = sx + sy * MX + sz * MX * MY
                    if not maskr[si] and Observation.ForwardMatches(rule, sx, sy, sz, potentials, t, MX, MY, backwards):
                        maskr[si] = True
                        Observation.ApplyForward(rule, sx, sy, sz, potentials, t, MX, MY, queue, backwards)

    @staticmethod
    def ForwardMatches(rule, x, y, z, potentials, t, MX, MY, backwards):
        dz = dy = dx = 0
        a = rule.output if backwards else rule.binput
        for di in range(len(a)):
            value = a[di]
            if value != 0xff:
                current = potentials[value][x + dx + (y + dy) * MX + (z + dz) * MX * MY]
                if current > t or current == -1:
                    return False
            dx += 1
            if dx == rule.IMX:
                dx = 0
                dy += 1
                if dy == rule.IMY:
                    dy = 0
                    dz += 1
        return True

    @staticmethod
    def AapplyForward(rule, x, y, z, potentials, t, MX, MY, q, backwards):
        a = rule.binput if backwards else rule.output
        for dz in range(rule.IMZ):
            zdz = z + dz
            for dy in range(rule.IMY):
                ydy = y + dy
                for dx in range(rule.IMX):
                    xdx = x + dx
                    idi = xdx + ydy * MX + zdz * MX * MY
                    di = dx + dy * rule.IMX + dz * rule.IMX * rule.IMY
                    o = a[di]
                    if o != 0xff and potentials[o][idi] == -1:
                        potentials[o][di] = t + 1
                        q.append((o, xdx, ydy, zdz))

    @staticmethod
    def IsGoalReached(present, future):
        for i in range(len(present)):
            if ((1 << present[i]) & future[i]) == 0:
                return False
        return True

    @staticmethod
    def ForwardPointwise(potentials, future):
        sum = 0
        for i in range(len(future)):
            f = future[i]
            min = 1000
            argmin = -1
            for c in range(len(potentials)):
                potential = potentials[c][i]
                if((f & 1) == 1 and potential >= 0 and potential < min):
                    min = potential
                    argmin = c
                f = f >> 1
            if argmin < 0:
                return -1
            sum += min
        return sum

    @staticmethod
    def BackwardPointwise(potentials, present):
        sum = 0
        for i in range(len(present)):
            potential = potentials[present[i]][i]
            if potential < 0:
                return -1
            sum += potential
        return sum
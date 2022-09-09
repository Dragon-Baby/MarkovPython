import XMLHelper as XH
import Node
# from abc import ABC, abstractmethod
import math
import random as rd
import sys
import Helper as He


class WFCNode(Node.Branch):
    DX = [1, 0, -1, 0, 0, 0]
    DY = [0, 1, 0, -1, 0, 0]
    DZ = [0, 0, 0, 0, 1, -1]

    
    def __init__(self):
        super().__init__()
        self.wave = None
        # propagator 传播
        self.propagator = [[[]]]
        self.P = self.N = 1
        self.stack = []
        self.stack_size = 0
        self.weights = []
        self.weight_log_weights = []
        self.sum_of_weights = self.sum_of_weight_log_weights = self.starting_entropy = 0.0  # entropy 熵
        self.new_grid = None
        self.start_wave = None
        self.map = {}
        self.periodic = self.shannon = False    # shannon 噪声类型
        self.distribution = []
        self.tries = 0
        self.name = ""
        self.firstgo = True
        self.random = 0

    def Load(self, xelem, parent_symmetry, grid):
        self.shannon = XH.GetValue(xelem, "shannon", False)
        self.tries = XH.GetValue(xelem, "tries", 1000)
        self.wave = Wave(len(grid.state), self.P, len(self.propagator), self.shannon)
        self.start_wave = Wave(len(grid.state), self.P, len(self.propagator), self.shannon)
        self.stack = [(0,0)]*len(self.wave.data)*self.P

        self.sum_of_weights = self.sum_of_weight_log_weights = self.starting_entropy = 0

        if self.shannon:
            self.weight_log_weights = [0.0] * self.P
            for t in range(self.P):
                self.weight_log_weights[t] = self.weights[t] * math.log(self.weights[t])
                self.sum_of_weights += self.weights[t]
                self.sum_of_weight_log_weights += self.weight_log_weights[t]

            self.starting_entropy = math.log(self.sum_of_weights) - self.sum_of_weight_log_weights / self.sum_of_weights
        
        self.distribution = [0.0] * self.P
        return super().Load(xelem, parent_symmetry, self.new_grid)

    def Reset(self):
        super().Reset()
        self.n = -1
        self.firstgo = True

    def Go(self):
        print("Go for Node:{0}".format(self))
        if self.n >= 0:
            return super().Go()
        if self.firstgo:
            self.wave.Init(self.propagator, self.sum_of_weights, self.sum_of_weight_log_weights, self.starting_entropy, self.shannon)
            for i in range(len(self.wave.data)):
                value = self.grid.state[i]
                if value in self.map.keys():
                    start_wave = self.map[value]
                    for t in range(self.P):
                        if not start_wave[t]:
                            self.Ban(i, t)
            first_success = self.Propagate()
            if not first_success:
                print("initial conditions are contradictive")   # contradictive 矛盾
                return False
            self.start_wave.CopyFrom(self.wave, len(self.propagator), self.shannon)
            goodseed = self.GoodSeed()
            if goodseed == None:
                return False
            rd.seed(goodseed)
            self.stack_size = 0
            self.wave.CopyFrom(self.start_wave, len(self.propagator), self.shannon)
            self.firstgo = False
            self.new_grid.Clear()
            self.ip.grid = self.new_grid
            return True
        else:
            node = self.NextUnobservedNode(self.random)
            if node >= 0:
                self.Observe(node, self.random)
                self.Propagate()
            else:
                self.n += 1
            if self.n >= 0 or self.ip.gif:
                self.UpdateState()
            return True

    def GoodSeed(self):
        for k in range(self.tries):
            observation_sofar = 0
            rd.seed(self.ip.random)
            seed = rd.randrange(0, sys.maxsize)
            self.random = seed
            self.stack_size = 0
            self.wave.CopyFrom(self.start_wave, len(self.propagator), self.shannon)
            while True:
                node = self.NextUnobservedNode(self.random)
                if node >= 0:
                    self.Observe(node, self.random)
                    observation_sofar += 1
                    success = self.Propagate()
                    if not success:
                        print("CONTRADICTION on try {0} with {1} observations".format(k, observation_sofar))
                        break
                else:
                    print("wfc found a good seed {0} on try {1} with {2} observations".format(seed, k, observation_sofar))
                    return seed

        print("wfc failed to find a good seed in {0} tries".format(self.tries))
        return None


    def NextUnobservedNode(self, random):
        MX = self.grid.MX
        MY = self.grid.MY
        MZ = self.grid.MZ
        min = 1E+4
        argmin = -1
        for z in range(MZ):
            for y in range(MY):
                for x in range(MX):
                    if not self.periodic and (x + self.N > MX or y + self.N > MY or z + 1 > MZ):
                        continue
                    i = x + y * MX + z * MX * MY
                    remaining_values = self.wave.sums_of_ones[i]
                    entropy = self.wave.entropies[i] if self.shannon else remaining_values
                    if remaining_values > 1 and entropy <= min:
                        rd.seed(random)
                        noise = 1E-6 * rd.uniform(0,1)
                        if entropy + noise < min:
                            min = entropy + noise
                            argmin = i
        return argmin

    
    def Observe(self, node, random):
        w = self.wave.data[node]
        for t in range(self.P):
            self.distribution[t] = self.weights[t] if w[t] else 0.0
        rd.seed(random)
        r = He.RandomWeights(self.distribution, rd.uniform(0,1))
        for t in range(self.P):
            if w[t] != (t == r):
                self.Ban(node, t)

    def Propagate(self):
        MX = self.grid.MX
        MY = self.grid.MY
        MZ = self.grid.MZ

        while self.stack_size > 0:
            (i1, p1) = self.stack[self.stack_size - 1]
            self.stack_size -= 1

            x1 = int(i1 % MX)
            y1 = int((i1 % (MX * MY)) / MX)
            z1 = int(i1 / (MX * MY))

            for d in range(len(self.propagator)):
                dx = WFCNode.DX[d]
                dy = WFCNode.DY[d]
                dz = WFCNode.DZ[d]
                x2 = x1 + dx
                y2 = y1 + dy
                z2 = z1 + dz
                if not self.periodic and (x2 < 0 or y2 < 0 or z2 < 0 or x2 + self.N > MX or y2 + self.N > MY or z2 + 1 > MZ):
                    continue
                if x2 < 0:
                    x2 += MX
                elif x2 >= MX:
                    x2 -= MX
                if y2 < 0:
                    y2 += MY
                elif y2 >= MY:
                    y2 -= MY
                if z2 < 0:
                    z2 += MZ
                elif z2 >= MZ:
                    z2 -= MZ

                i2 = x2 + y2 * MX + z2 * MX * MY
                p = self.propagator[d][p1]
                compat = self.wave.compatible[i2]

                for l in range(len(p)):
                    t2 = p[l]
                    comp = compat[t2]
                    comp[d] -= 1
                    if comp[d] == 0:
                        self.Ban(i2, t2)

        return self.wave.sums_of_ones[0] > 0

    
    def Ban(self, i, t):
        self.wave.data[i][t] = False
        comp = self.wave.compatible[i][t]
        for d in range(len(self.propagator)):
            comp[d] = 0
        self.stack[self.stack_size] = (i, t)
        self.stack_size += 1

        self.wave.sums_of_ones[i] -= 1
        if self.shannon:
            sum = self.wave.sums_of_weights[i]
            self.wave.entropies[i] += self.wave.sums_of_weight_log_weights[i] / sum - math.log(sum)

            self.wave.sums_of_weights[i] -= self.weights[t]
            self.wave.sums_of_weight_log_weights[i] -= self.weight_log_weights[t]

            sum = self.wave.sums_of_weights[i]
            self.wave.entropies[i] -= self.wave.sums_of_weight_log_weights[i] / sum - math.log(sum)


    # @abstractmethod
    def UpdateState(self):
        pass

    


class Wave():
    opposite = [2,3,0,1,5,4]
    def __init__(self, length, P, D, shannon):
        self.data = [[True] * P] * length
        self.compatible = [[[-1]*D]*P]*length
        self.sums_of_ones = [0] * length
        self.sums_of_weights = self.sums_of_weight_log_weights = self.entropies = []
        if shannon:
            self.sums_of_weights = [0.0] * length
            self.sums_of_weight_log_weights = [0.0] * length
            self.entropies = [0.0] * length

    def Init(self, propagator, sum_of_weights, sum_of_weight_log_weights, starting_entropy, shannon):
        P = len(self.data[0])
        for i in range(len(self.data)):
            for p in range(P):
                self.data[i][p] = True
                for d in range(len(propagator)):
                    self.compatible[i][p][d] = len(propagator[Wave.opposite[d]][p])
                self.sums_of_ones[i] = P
                if shannon:
                    self.sums_of_ones[i] = sum_of_weights
                    self.sums_of_weight_log_weights[i] = sum_of_weight_log_weights
                    self.entropies[i] = starting_entropy

    def CopyFrom(self, wave, D, shannon):
        for i in range(len(self.data)):
            datai = self.data[i]
            wave_datai = wave.data[i]
            for t in range(len(datai)):
                datai[t] = wave_datai[t]
                for d in range(D):
                    self.compatible[i][t][d] = wave.compatible[i][t][d]
            self.sums_of_ones[i] = wave.sums_of_ones[i]
            if shannon:
                self.sums_of_ones[i] = wave.sums_of_weights[i]
                self.sums_of_weight_log_weights[i] = wave.sums_of_weight_log_weights[i]
                self.entropies[i] = wave.entropies[i]
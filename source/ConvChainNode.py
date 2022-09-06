import XMLHelper as XH
from Node import Node
import Graphics
import Helper as He
import SymmetryHelper as SH
import random as rd
import math

class ConvChainNode(Node):
    def __init__(self):
        super().__init__()
        self.N = 0
        self.temperature = 0.0
        self.weights = []
        self.c0 = self.c1 = 0
        self.substrate = []
        self.substrate_color = 0
        self.counter = self.steps = 0

        self.sample = []
        self.SMX = self.SMY = 0

    def Load(self, xelem, symmetry, grid):
        if grid.MZ != 1:
            print("convchain currently works only for 2d")
            return False
        name = XH.GetValue(xelem, "sample", "")
        filename = "resources/samples/{0}.png".format(name)
        bitmap = []
        (bitmap, self.SMX, self.SMY, _) = Graphics.LoadBitmap(filename)
        if bitmap == []:
            print("couldn't load ConvChain sample {0}".format(filename))
            return False
        self.sample = [False] * len(bitmap)
        for i in range(len(self.sample)):
            self.sample[i] = bitmap[i] == -1

        self.N = XH.GetValue(xelem, "n", 3)
        self.steps = XH.GetValue(xelem, "steps", -1)
        self.c0 = grid.values[XH.GetValue(xelem, "black", "")]
        self.c1 = grid.values[XH.GetValue(xelem, "white", "")]
        self.substrate_color = [False] * len(grid.state)
        self.weights = [0.0] * (1 << (self.N * self.N))
        for y in range(self.SMY):
            for x in range(self.SMX):
                pattern = He.Pattern(lambda dx, dy : self.sample[(x + dx) % self.SMX + (y + dy) % self.SMY * self.SMX], self.N)
                symmetries = SH.SquareSymmetries(pattern, lambda q : He.Rotated(q, self.N), lambda q : He.Reflected(q, self.N), lambda q1, q2 : False, symmetry)
                for q in symmetries:
                    self.weights[He.IndexBoolArray(q)] += 1
        for k in range(len(self.weights)):
            if self.weights[k] <= 0:
                self.weights[k] = 0.1
        return True

    
    def Toggle(self, state, i):
        state[i] = self.c1 if state[i] == self.c0 else self.c0

    def Go(self):
        if self.steps > 0 and self.counter >= self.steps:
            return False
        MX = self.grid.MX
        MY = self.grid.MY
        state = self.grid.state

        if self.counter == 0:
            any_substrate = False
            for i in range(len(self.substrate)):
                if state[i] == self.substrate_color:
                    rd.seed(self.ip.random)
                    state[i] = self.c0 if rd.randrange(0, 2) == 0 else self.c1
                    self.substrate[i] = True
                    any_substrate = True
            self.counter += 1
            return any_substrate

        for k in range(len(state)):
            rd.seed(self.ip.random)
            r = rd.randrange(0, len(state))
            if not self.substrate[r]:
                continue
            x = int(r % MX)
            y = int(r / MX)
            q = 1.0

            for sy in range(y - self.N + 1, y + self.N):
                for sx in range(x - self.N + 1, x + self.N):
                    ind = difference = 0
                    for dy in range(self.N):
                        for dx in range(self.N):
                            X = sx + dx
                            if X < 0:
                                X += MX
                            elif X >= MX:
                                X -= MX
                            
                            Y = sy + dy
                            if Y < 0:
                                Y += MY
                            elif Y >= MY:
                                Y -= MY

                            value = state[X + Y * MX] == self.c1
                            power = 1 << (dy * self.N + dx)
                            ind += power if value else 0
                            if X == x and Y == y:
                                difference = power if value else -power
                    q *= self.weights[ind - difference] / self.weights[ind]

            if q >= 1:
                self.Toggle(state, r)
                continue
            if self.temperature != 1:
                q = math.pow(q, 1.0 / self.temperature)
            if q > rd.uniform(0,1):
                self.Toggle(state, r)           
        self.counter += 1
        return True

    def Reset(self):
        for i in range(len(self.substrate)):
            self.substrate[i] = False
        self.counter = 0
import XMLHelper as XH

class Grid():
    def __init__(self):
        self.state = []
        self.mask = []
        self.MX = 0
        self.MY = 0
        self.MZ = 0

        self.C = 0
        self.characters = []
        self.values = {}
        self.waves = {}
        self.folder = ""

        self.transparent = 0
        self.statebuffer = []

    @staticmethod
    def Load(xelem, MX, MY, MZ):
        g = Grid()
        g.MX = MX
        g.MY = MY
        g.MZ = MZ
        value_str = XH.GetValue(xelem, "values", "")
        if value_str != "":
            value_str = value_str.replace(" ", "")
        if value_str == "":
            print("no values specified")
            return None

        print("gridvalues", value_str)

        g.C = len(value_str)
        g.values = {}
        g.waves = {}
        g.characters = [''] * g.C
        for i in range(g.C):
            i = i
            symbol = value_str[i]
            if symbol in g.values.keys():
                print("repeating value {0} at line {1}".format(symbol, xelem._start_line_number))
                return None
            else:
                g.characters[i] = symbol
                g.values[symbol] = i
                g.waves[symbol] = (1 << i) & 0xff

        trans_str = XH.GetValue(xelem, "trasparent", "")
        if trans_str != "":
            g.transparent = g.Wave(trans_str)

        xunions = filter(lambda x : x.tag == "union", list(iter(XH.MyDescendants(xelem, ["markov", "sequence", "union"]))))
        g.waves["*"] = ((1 << g.C) - 1) & 0xff
        for xunion in xunions:
            symbol = XH.GetValue(xunion, "symbol", "")
            if symbol in g.waves.keys():
                print("repeating union type {0} at line {1}".format(symbol, xunion._start_line_number))
                return None
            else:
                w = g.Wave(XH.GetValue(xunion, "values", ""))
                g.waves[symbol] = w

        g.state = [0]*MX*MY*MZ
        g.statebuffer = [0]*MX*MY*MZ
        g.mask = [True]*MX*MY*MZ
        g.folder = XH.GetValue(xelem, "folder", "")
        return g

    def Wave(self, values):
        sum = 0
        for k in range(len(self.values)):
            sum += (1 << self.values[values[k]])
        return sum

    def Clear(self):
        for i in range(len(self.state)):
            self.state[i] = 0

    def Matches(self, rule, x, y, z): 
        dz = dy = dx = 0
        for di in range(len(rule.input)):
            if (rule.input[di] & (1 << self.state[x + dx + (y + dy) * self.MX + (z + dz) * self.MX * self.MY])) == 0:
                return False
            dx += 1
            if dx == rule.IMX:
                dx = 0
                dy += 1
                if dy == rule.IMY:
                    dy = 0
                    dz += 1
        return True
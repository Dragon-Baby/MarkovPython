from source import XMLHelper as XH
from source import SymmetryHelper as SH
from source import Grid
from source import Node
from source import Branch
from source import MarkovNode



class Interpreter():
    def __init__(self):
        # branch node
        self.root = None
        self.current = None
        # go grid
        self.grid = None
        self.start_grid = None
        
        self.random = 0
        self.origin = False

        self.changes = []
        self.first = []
        self.counter = 0

        self.gif = False

    @staticmethod
    def Load(xelem, MX, MY, MZ):
        ip = Interpreter()
        ip.origin = XH.GetValue(xelem, "origin", False)
        
        # grid
        ip.grid = Grid.Load(xelem, MX, MY, MZ)
        if ip.grid == None:
            print("failed to load grid")
            return None
        ip.start_grid = ip.grid

        symmetry_str = XH.GetValue(xelem, "symmetry", "")
        # get symmetry
        symmetry = SH.GetSymmetry(ip.grid.MZ == 1, symmetry_str, [True]*(8 if ip.grid.MZ == 1 else 48))
        if symmetry == []:
            print("unknown symmetry {0} at line {1}".format(symmetry_str, xelem._start_line_number))
            return None

        # node
        top_node = Node.Factory(xelem, symmetry, ip, ip.grid)
        if top_node == None:
            return None

        ip.root = top_node if type(top_node) == Branch else MarkovNode(top_node, ip)
        ip.changes = []
        ip.first = []
        return ip


    def Run(self, seed, steps, gif):
        self.random = seed
        self.grid = self.start_grid
        self.grid.Clear()
        if self.origin:
            self.grid.state[self.grid.MX / 2 + (self.grid.MY / 2) * self.grid.MX + (self.grid.MZ / 2) * self.grid.MX * self.grid.MY] = 1
        
        self.changes = []
        self.first = []
        self.first.append(0)

        self.root.Reset()
        self.current = self.root

        self.gif = gif
        self.counter = 0

        while(self.current != None and (steps <= 0 or self.counter < steps)):
            if gif:
                print("[{0}]".format(self.counter))
                yield (self.grid.state, self.grid.characters, self.grid.MX, self.grid.MY, self.grid.MZ)
            
            self.current.Go()
            self.counter += 1
            self.first.append(len(self.changes))

        yield self.grid.state, self.grid.characters, self.grid.MX, self.grid.MY, self.grid.MZ

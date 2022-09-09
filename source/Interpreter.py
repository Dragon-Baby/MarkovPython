import sys
sys.modules['_elementtree'] = None
import XMLHelper as XH
import SymmetryHelper as SH

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
        
        import Grid
        import Node
        # grid
        ip.grid = Grid.Grid.Load(xelem, MX, MY, MZ)
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

        print(xelem)
        # node
        top_node = Node.Node.Factory(xelem, symmetry, ip, ip.grid)
        print(top_node)
        if top_node == None:
            return None

        # print(type(top_node).__bases__, Node.Branch)
        ip.root = top_node if (Node.Branch in type(top_node).__bases__) else Node.MarkovNode(top_node, ip)
        ip.changes = []
        ip.first = []
        return ip


    def Run(self, seed, steps, gif):
        print("Here!")
        self.random = seed
        self.grid = self.start_grid
        self.grid.Clear()
        if self.origin:
            self.grid.state[int(self.grid.MX / 2) + int(self.grid.MY / 2) * self.grid.MX + int(self.grid.MZ / 2) * self.grid.MX * self.grid.MY] = 1
        
        self.changes = []
        self.first = []
        self.first.append(0)

        print("root", self.root)
        self.root.Reset()
        self.current = self.root

        self.gif = gif
        self.counter = 0

        while(self.current != None and (steps <= 0 or self.counter < steps)):
            if gif:
                print("[{0}]".format(self.counter))
                yield (self.grid.state, self.grid.characters, self.grid.MX, self.grid.MY, self.grid.MZ)
            
            print("While Here!")
            print("Go:",self.current.Go())
            self.counter += 1
            self.first.append(len(self.changes))

        yield self.grid.state, self.grid.characters, self.grid.MX, self.grid.MY, self.grid.MZ

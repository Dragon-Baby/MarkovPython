import sys
sys.modules['_elementtree'] = None
import XMLHelper as XH
import SymmetryHelper as SH

class Interpreter():
    def __init__(self):
        # branch node
        self.root = None    # Branch    
        self.current = None # Branch
        # go grid
        self.grid = None    # Grid
        self.start_grid = None  # Grid
        
        self.random = 0     # seed for random
        self.origin = False     # bool

        self.changes = []   # list for (int, int, int)
        self.first = []     # list for int
        self.counter = 0    # int

        self.gif = False    # bool

    # return Interpreter
    @staticmethod
    def Load(xelem, MX, MY, MZ):
        ip = Interpreter()
        ip.origin = XH.GetValue(xelem, "origin", False)
        
        import Grid
        import Node
        # grid
        print("[Grid] > Start Loading Grid!")
        ip.grid = Grid.Grid.Load(xelem, MX, MY, MZ)
        if ip.grid == None:
            print("[Grid] > !!! Failed to Load Grid !!!")
            return None

        print("[Grid] > Finished !")
        ip.start_grid = ip.grid

        symmetry_str = XH.GetValue(xelem, "symmetry", "")
        print("[Interpreter] > Get Symmetry for {0}".format(symmetry_str))
        # get symmetry
        symmetry = SH.GetSymmetry(ip.grid.MZ == 1, symmetry_str, [True for i in range(8 if ip.grid.MZ == 1 else 48)])
        if symmetry == []:
            print("[Interpreter] > Unknown Symmetry {0} at line {1}".format(symmetry_str, xelem._start_line_number))
            return None

        print("[Node] > Start Creating Top Node!")
        # node
        top_node = Node.Node.Factory(xelem, symmetry, ip, ip.grid)
        if top_node == None:
            print("[Node] > !!! Failed to Create Top Node !!!")
            return None

        print("[Node] > Success to Create Top Node!")
        ip.root = top_node if (Node.Branch in type(top_node).__bases__) else Node.MarkovNode(top_node, ip)
        print("[Interpreter] > Root Node as {0}".format(ip.root))
        ip.changes = []
        ip.first = []
        return ip


    # Enumerable
    # return list,list,int,int,int
    def Run(self, seed, steps, gif):
        self.random = seed
        self.grid = self.start_grid
        self.grid.Clear()
        if self.origin:
            self.grid.state[int(self.grid.MX / 2) + int(self.grid.MY / 2) * self.grid.MX + int(self.grid.MZ / 2) * self.grid.MX * self.grid.MY] = 1
        
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

from source import XMLHelper as XH
from source import SymmetryHelper as SH
from source import OneNode
from source import AllNode
from source import ParallelNode
from source import PathNode
from source import MapNode
from source import ConvolutionNode
from source import ConvChainNode
from source import WFCNode
from source import OverlapNode
from source import TileNode


class Node():
    node_names = ["one", "all", "prl", "markov", "sequence", "path", "map", "convolution", "convchain", "wfc"]
    def __init__(self):
        self.ip = None
        self.grid = None

    def Load(self, xelem, symmetry, grid):
        return True

    def Reset(self):
        pass

    def Go(self):
        return True

    @staticmethod
    def Factory(xelem, symmetry, ip, grid):
        if not xelem.tag in Node.node_names:
            print("unknown node type \"{0}\" at line {1}".format(xelem.tag, xelem._start_line_number))
            return None
        
        result = None
        name = xelem.tag
        if name == "one":
            result = OneNode()
        elif name == "all":
            result = AllNode()
        elif name == "prl":
            result = ParallelNode()
        elif name == "markov":
            result = MarkovNode()
        elif name == "sequence":
            result = SequenceNode()
        elif name == "path":
            result = PathNode()
        elif name == "map":
            result = MapNode()
        elif name == "convolution":
            result = ConvolutionNode()
        elif name == "convchain":
            result = ConvChainNode()
        elif name == "wfc" and XH.GetValue(xelem, "sample", "") != "":
            result = OverlapNode()
        elif name == "wfc" and XH.GetValue(xelem, "tileset", "") != "":
            result = TileNode()
        else:
            result = None

        result.ip = ip
        result.grid = grid
        success = result.Load(xelem, symmetry. grid)

        if not success:
            return None
        return result



class Branch(Node):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.nodes = []
        self.n = 0

    def Load(self, xelem, parent_symmetry, grid):
        symmetry_str = XH.GetValue(xelem, "symmetry", "")
        symmetry = SH.GetSymmetry(self.ip.grid.MZ==1, symmetry_str, parent_symmetry)
        if symmetry == []:
            print("unknown symmetry {0} at line {1}".format(symmetry_str, xelem._start_line_number))
            return False
        
        xchildren = XH.Elements(Branch.node_names)
        self.nodes = [None] * len(xchildren)
        for c in range(len(xchildren)):
            child = Branch.Load(xchildren[c], symmetry, self.ip, grid)
            if child == None:
                return False
            if type(child) == Branch:
                child.parent = None if type(child) is MapNode or type(child) is WFCNode else self
            self.nodes[c] = child

        return True

    def Go(self):
        while self.n < len(self.nodes):
            node = self.nodes[self.n]
            if type(node) is Branch:
                self.ip.current = self.node
            if node.Go():
                return True
            self.n += 1
        self.ip.current = self.ip.current.parent
        self.Reset()
        return False

    def Reset(self):
        for node in self.nodes:
            node.Reset()
        self.n = 0


class SequenceNode(Branch):
    def __init__(self):
        super().__init__()

class MarkovNode(Branch):
    def __init__(self, child=None, ip=None):
        super().__init__()
        self.nodes = [child]
        self.ip = ip
        self.grid = ip.grid

    def Go(self):
        self.n = 0
        return super().Go()
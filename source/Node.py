import XMLHelper as XH
import SymmetryHelper as SH


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
        import OneNode
        import AllNode
        import ParallelNode
        import PathNode
        import MapNode
        import ConvolutionNode
        import ConvChainNode
        import OverlapNode
        import TileNode
        if not xelem.tag in Node.node_names:
            print("unknown node type \"{0}\" at line {1}".format(xelem.tag, xelem._start_line_number))
            return None
        
        result = None
        name = xelem.tag
        if name == "one":
            result = OneNode.OneNode()
        elif name == "all":
            result = AllNode.AllNode()
        elif name == "prl":
            result = ParallelNode.ParallelNode()
        elif name == "markov":
            result = MarkovNode()
        elif name == "sequence":
            result = SequenceNode()
        elif name == "path":
            result = PathNode.PathNode()
        elif name == "map":
            result = MapNode.MapNode()
        elif name == "convolution":
            result = ConvolutionNode.ConvolutionNode()
        elif name == "convchain":
            result = ConvChainNode.ConvChainNode()
        elif name == "wfc" and XH.GetValue(xelem, "sample", "") != "":
            result = OverlapNode.OverlapNode()
        elif name == "wfc" and XH.GetValue(xelem, "tileset", "") != "":
            result = TileNode.TileNode()
        else:
            result = None
        result.ip = ip
        result.grid = grid
        print(result)
        success = result.Load(xelem, symmetry, grid)
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
        
        xchildren = XH.Elements(xelem, Node.node_names)
        self.nodes = [None] * len(xchildren)
        import MapNode
        import WFCNode
        for c in range(len(xchildren)):
            child = Node.Factory(xchildren[c], symmetry, self.ip, grid)
            print(child)
            if child == None:
                return False
            if type(child) == Branch:
                child.parent = None if type(child) is MapNode.MapNode or (WFCNode.WFCNode in type(child).__bases__) else self
            self.nodes[c] = child

        return True

    def Go(self):
        print("Go for Node:{0}".format(self))
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
        self.grid = self.ip.grid

    def Go(self):
        print("Go for Node:{0}".format(self))
        self.n = 0
        return super().Go()
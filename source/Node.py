import XMLHelper as XH
import SymmetryHelper as SH


class Node():
    node_names = ["one", "all", "prl", "markov", "sequence", "path", "map", "convolution", "convchain", "wfc"]

    def __init__(self):
        self.ip = None  # Interpreter
        self.grid = None    # Grid
        self.start_line = -1 

    def Load(self, xelem, symmetry, grid):
        return True

    def Reset(self):
        pass

    def Go(self):
        return True

    # return Node
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
            print("[Node] > Unknown Node Type \"{0}\" at line {1}".format(xelem.tag, xelem._start_line_number))
            return None
        
        result = None
        name = xelem.tag
        print("[Node] > Node Name : [{0}] at line {1}".format(name, xelem._start_line_number))
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
        result.start_line = xelem._start_line_number
        success = result.Load(xelem, symmetry, grid)
        if not success:
            print("[Node] > Failed to Loading {0} at line {1}".format(result, result.start_line))
            return None
        return result



class Branch(Node):
    def __init__(self):
        super().__init__()
        print("[Branch] > {0} Factory as a Branch".format(self))
        self.parent = None  # Branch
        self.nodes = [] # list of Node
        self.n = 0  # int

    # load child nodes from xml
    def Load(self, xelem, parent_symmetry, grid):
        print("[Branch] > {0} Load as a Branch".format(self))
        symmetry_str = XH.GetValue(xelem, "symmetry", "")
        symmetry = SH.GetSymmetry(self.ip.grid.MZ==1, symmetry_str, parent_symmetry)
        if symmetry == []:
            print("[Branch] > !!! Unknown Symmetry {0} at line {1}".format(symmetry_str, xelem._start_line_number))
            return False
        
        xchildren = XH.Elements(xelem, Node.node_names)
        print("[Branch] > Child Elements : {0}".format(xchildren))
        self.nodes = [None for i in range(len(xchildren))]
        import MapNode
        import WFCNode
        print("[Branch] > Start Creating Child Nodes!")
        for c in range(len(xchildren)):
            print("[Branch] > Factory Child Node for {0} at line {1}".format(xchildren[c], xchildren[c]._start_line_number))
            child = Node.Factory(xchildren[c], symmetry, self.ip, grid)
            if child == None:
                print("[Branch] > !!! Failed to Create Child Node {0} at line {1}".format(xchildren[c], xchildren[c]._start_line_number))
                return False
            if Branch in type(child).__bases__:
                child.parent = None if type(child) is MapNode.MapNode or (WFCNode.WFCNode in type(child).__bases__) else self
            self.nodes[c] = child

        return True

    def Go(self):
        while self.n < len(self.nodes):
            node = self.nodes[self.n]
            if Branch in type(node).__bases__:
                self.ip.current = node
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
        print("[SequenceNode] > Factory a SequenceNode")
        super().__init__()

class MarkovNode(Branch):
    def __init__(self, child=None, ip=None):
        super().__init__()
        self.nodes = [child]
        self.ip = ip
        self.grid = ip.grid if ip != None else None

    def Go(self):
        self.n = 0
        return super().Go()
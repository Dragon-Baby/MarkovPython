import XMLHelper as XH
from WFCNode import WFCNode

class TileNode(WFCNode):
    def __init__(self):
        super().__init__()
        self.tiledata = []
        self.S = self.SZ = 0
        self.overlap = self.overlapz = 0

    def Load(xelem, parent_symmetry, grid):
        pass

    def UpdateState(self):
        pass
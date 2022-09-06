import XMLHelper as XH
from WFCNode import WFCNode
import random as rd
import xml.etree.ElementTree as ET
import VoxHelper as VH

class TileNode(WFCNode):
    def __init__(self):
        super().__init__()
        self.tiledata = []
        self.S = self.SZ = 0
        self.overlap = self.overlapz = 0

    def Load(self, xelem, parent_symmetry, grid):
        self.periodic = XH.GetValue(xelem, "periodic", False)
        self.name = XH.GetValue(xelem, "tileset", "")
        tilesname = XH.GetValue(xelem, "tiles", self.name)
        self.overlap = XH.GetValue(xelem, "overlap", 0)
        self.overlapz = XH.GetValue(xelem, "overlapz", 0)

        xdoc = None
        filepath = "resources/tilesets/{0}.xml".format(self.name)
        try:
            xdoc = ET.parse(filepath, parser=XH.LineNumberingParser())
        except:
            print("couldm't open tileset {0}".format(filepath))
            return False
        
        xroot = xdoc.getroot()

        full_symmetry = XH.GetValue(xroot, "fullSymmetry", False)
        xfirst_tile = xroot.find("./tiles").find("./tile")
        first_filename = "{0}/{1}.vox".format(tilesname, XH.GetValue(xfirst_tile, "name", ""))
        first_data = []
        SY = 0
        (first_data, self.S, SY, self.SZ) = VH.LoadVox("resources/tilesets/{0}".format(first_filename))
        if first_data == []:
            print("couldn't read {0}".format(first_filename))
            return False
        if self.S != SY:
            print("tiles should be square shaped: {0} != {1}".format(self.S, SY))
            return False
        if full_symmetry and self.S != self.SZ:
            print("tiles should be cubes for the full symmetry option : {0} != {1}".format(self.S, self.SZ))
            return False
        



    def UpdateState(self):
        for z in range(self.grid.MZ):
            for y in range(self.grid.MY):
                for x in range(self.grid.MX):
                    w = self.wave.data[x + y * self.grid.MX + z * self.grid.MX * self.grid.MY]
                    votes = [[0]*self.new_grid.C] * self.S * self.S * self.SZ
                    for t in range(self.P):
                        if w[t]:
                            tile = self.tiledata[t]
                            for dz in range(self.SZ):
                                for dy in range(self.S):
                                    for dx in range(self.S):
                                        di = dx + dy * self.S + dz * self.S * self.S
                                        votes[di][tile[di]] += 1
                    
                    for dz in range(self.SZ):
                        for dy in range(self.S):
                            for dx in range(self.S):
                                v = votes[dx + dy * self.S + dz * self.S * self.S]
                                max = -1.0
                                argmax = 0xff
                                for c in range(len(v)):
                                    vote = v[c] + 0.1 * rd.random()
                                    if vote > max:
                                        argmax = c
                                        max = vote
                                sx = x * (self.S - self.overlap) + dx
                                sy = y * (self.S - self.overlap) + dy
                                sz = z * (self.S - self.overlapz) + dz
                                self.new_grid.state[sx + sy * self.new_grid.MX + sz * self.new_grid.MX * self.new_grid.MY] = argmax
import XMLHelper as XH
from WFCNode import WFCNode
import random as rd
import xml.etree.ElementTree as ET
import VoxHelper as VH
from Grid import Grid
import Helper as He
import SymmetryHelper as SH
from source.SymmetryHelper import SquareSymmetries

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
        
        self.new_grid = Grid.Load(xelem, (self.S - self.overlap) * grid.MX + self.overlap, (self.S - self.overlap) * grid.MY + self.overlap, (self.SZ - self.overlap) * grid.MZ + self.overlap)
        if self.new_grid == None:
            return False

        self.tiledata = []
        positions = {}
        def newtile(f):
            return [[[f]*self.SZ]*self.S]*self.S

        def xRotate(p):
            return newtile(lambda x, y, z : p[y + (self.S - 1 - x) * self.S + z * self.S * self.S])
        
        def yRotate(p):
            return newtile(lambda x, y, z : p[z + y * self.S + (self.S - 1 - x) * self.S * self.S])

        def zRotate(p):
            return newtile(lambda x, y, z : p[x + z * self.S + (self.S - 1 - x) * self.S * self.S])

        def xReflect(p):
            return newtile(lambda x, y, z : p[(self.S - 1 - x) + y * self.S + z * self.S * self.S])

        def yReflect(p):
            return newtile(lambda x, y, z : p[x + (self.S - 1 - y) * self.S + z * self.S * self.S])

        def zReflect(p):
            return newtile(lambda x, y, z : p[x + y * self.S + (self.S - 1 - z) * self.S * self.S])

        named_tile_data = {}
        temp_stationary = []

        uniques = []
        xtiles = XH.Elements(xroot.find("./tiles"), ["tile"])
        ind = 0
        for xtile in xtiles:
            tilename = XH.GetValue(xtile, "name", "")
            weight = XH.GetValue(xtile, "weight", 1.0)

            filename = "resources/tilesets/{0}/{1}.vox".format(tilesname, tilename)
            vox = VH.LoadVox(filename)[0]
            if vox == []:
                print("couldn't read tile {0}".format(filename))
                return False
            (flat_tile, C) = He.Ords(vox, uniques)
            if C > self.new_grid.C:
                print("there were more than {0} colors in vos files".format(self.new_grid.C))
                return False
            
            localdata = SH.CubeSymmetries(flat_tile, zRotate, yRotate, xReflect, He.Same) if full_symmetry else SH.SquareSymmetries(flat_tile, zRotate, xReflect, He.Same)

            position = [False] * 128
            named_tile_data[tilename] = localdata
            for p in localdata:
                self.tiledata.append(p)
                temp_stationary.append(weight)
                position[ind] = True
                ind += 1

            positions[tilename] = position

        self.P = len(self.tiledata)
        print("P = {0}".format(self.P))
        self.weights = temp_stationary

        map = {}
        for xrule in xelem.findall("./rule"):
            input = XH.GetValue(xrule, "in", "")
            outputs = XH.GetValue(xrule, "out", "").split("|")
            position = [False] * self.P
            for s in outputs:
                array = []
                if s in positions.keys():
                    array = positions[s]
                else:
                    print("unknown tilename {0} at line {1}".format(xrule._start_line_number))
                    return False
                for p in range(self.P):
                    if array[p]:
                        position[p] = True
            map[grid.values[input]] = position

        if not 0 in map.keys():
            map[0] = [True] * self.P

        temp_propagator = [[[False] * self.P] * self.P] * 6

        def index(p):
            for i in range(len(self.tiledata)):
                if He.Same(p, self.tiledata[i]):
                    return i

        def last(attr):
            return attr.split(" ")[-1]

        def tile(attr):
            code = attr.split(" ")
            action = code[0] if len(code) == 2 else ""
            starttile = named_tile_data[last(attr)][0]
            i = len(action) - 1
            while i >= 0:
                sym = action[i]
                if sym == "x":
                    starttile = xRotate(starttile)
                elif sym == "y":
                    starttile = yRotate(starttile)
                elif sym == "z":
                    starttile = zRotate(starttile)
                else:
                    print("unknown symmetry {0}".format(sym))
                    return []
                i -= 1
            return starttile

        tilenames = list(map(lambda x : XH.GetValue(x, "name", ""), xtiles))
        tilenames.append("")

        for xneighbor in xroot.find("./neighbors").findall("./neighbor"):
            if full_symmetry:
                left = XH.GetValue(xneighbor, "left", "")
                right = XH.GetValue(xneighbor, "right", "")
                if not last(left) in tilenames or not last(right) in tilenames:
                    print("unknown tile {0} or {1} at line {2}".format(last(left), last(right), xneighbor._start_line_number))
                    return False
                
                ltile = tile(left)
                rtile = tile(right)
                if ltile == [] or rtile == []:
                    return False

                lsym = SH.SquareSymmetries(ltile, xRotate, yReflect, lambda p1, p2 : False)
                rsym = SH.SquareSymmetries(rtile, xRotate, yReflect, lambda p1, p2 : False)

                for i in range(len(lsym)):
                    temp_propagator[0][index(lsym[i])][index(rsym[i])] = True
                    temp_propagator[0][index(xReflect(rsym[i]))][index(xReflect(lsym[i]))] = True
                
                dtile = zRotate(ltile)
                utile = zRotate(rtile)

                dsym = SH.SquareSymmetries(dtile, yRotate, zReflect, lambda p1, p2 : False)
                usym = SH.SquareSymmetries(utile, yRotate, zReflect, lambda p1, p2 : False)

                for i in range(len(dsym)):
                    temp_propagator[1][index(dsym[i])][index(usym[i])] = True
                    temp_propagator[1][index(yReflect(usym[i]))][index(yReflect(dsym[i]))] = True

                btile = zRotate(ltile)
                ttile = zRotate(rtile)

                bsym = SH.SquareSymmetries(btile, zRotate, xReflect, lambda p1, p2 : False)
                tsym = SH.SquareSymmetries(ttile, zRotate, xReflect, lambda p1, p2 : False)

                for i in range(len(bsym)):
                    temp_propagator[4][index(bsym[i])][index(tsym[i])] = True
                    temp_propagator[4][index(zReflect(tsym[i]))][index(zReflect(bsym[i]))] = True

            elif XH.GetValue(xneighbor, "left", "") != "":
                left = XH.GetValue(xneighbor, "left", "")
                right = XH.GetValue(xneighbor, "right", "")

                if not last(left) in tilenames or not last(right) in tilenames:
                    print("unknown tile {0} or {1} at line {2}".format(last(left), last(right), xneighbor._start_line_number))
                    return False

                ltile = tile(left)
                rtile = tile(right)
                if ltile == [] or rtile == []:
                    return False

                temp_propagator[0][index(ltile)][index(rtile)] = True
                temp_propagator[0][index(yReflect(ltile))][index(yReflect(rtile))] = True
                temp_propagator[0][index(xReflect(rtile))][index(xReflect(ltile))] = True
                temp_propagator[0][index(yReflect(xReflect(rtile)))][index(yReflect(xReflect(ltile)))] = True


                dtile = zRotate(ltile)
                utile = zRotate(rtile)

                temp_propagator[0][index(dtile)][index(utile)] = True
                temp_propagator[0][index(yReflect(dtile))][index(yReflect(utile))] = True
                temp_propagator[0][index(xReflect(utile))][index(xReflect(dtile))] = True
                temp_propagator[0][index(yReflect(xReflect(utile)))][index(yReflect(xReflect(dtile)))] = True

            else:
                top = XH.GetValue(xneighbor, "top", "")
                bottom = XH.GetValue(xneighbor, "bottom", "")

                if not last(top) in tilenames or not last(bottom) in tilenames:
                    print("unknown tile {0} or {1} at line {2}".format(last(top), last(bottom), xneighbor._start_line_number))
                    return False

                ttile = tile(top)
                ntile = tile(bottom)

                if ttile == [] or btile == []:
                    return False

                bsym = SH.SquareSymmetries(btile, zRotate, xReflect, lambda p1, p2 : False)
                tsym = SH.SquareSymmetries(ttile, zRotate, xReflect, lambda p1, p2 : False)

                for i in range(len(tsym)):
                    temp_propagator[4][index(bsym[i])][index(tsym[i])] = True

        for p2 in range(self.P):
            for p1 in range(self.P):
                temp_propagator[2][p2][p1] = temp_propagator[0][p1][p2]
                temp_propagator[3][p2][p1] = temp_propagator[1][p1][p2]
                temp_propagator[5][p2][p1] = temp_propagator[4][p1][p2]

        sparse_propagator = [[[]]] * 6
        for d in range(6):
            sparse_propagator[d] = [[]] * self.P
            for t in range(self.P):
                sparse_propagator[d][t] = []

        self.propagator = [[[]]] * 6
        for d in range(6):
            self.propagator[d] = [[]] * self.P
            for p1 in range(self.P):
                sp = sparse_propagator[d][p1]
                tp = temp_propagator[d][p1]

                for p2 in range(self.P):
                    if tp[p2]:
                        sp.append(p2)

                ST = len(sp)
                self.propagator[d][p1] = [0] * ST
                for st in range(ST):
                    self.propagator[d][p1][st] = sp[st]

        return super().Load(xelem, parent_symmetry, grid)



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
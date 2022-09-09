import Node
import XMLHelper as XH
import Helper as He
import random as rd
import sys
import math

class PathNode(Node.Node):
    def __init__(self):
        super().__init__()
        self.start = self.finish = self.substrate = 0
        self.value = 0
        # inertia 惰性 惯性
        self.inertia = self.longest = self.edges = self.vertices = False

    def Load(self, xelem, parent_symmetry, grid):
        start_symbols = XH.GetValue(xelem, "from", "")
        self.start = grid.Wave(start_symbols)
        self.value = grid.values[XH.GetValue(xelem, "color", start_symbols[0])]
        self.finish = grid.Wave(XH.GetValue(xelem, "to", ""))
        self.inertia = XH.GetValue(xelem, "inertia", False)
        self.longest = XH.GetValue(xelem, "longest", False)
        self.edges = XH.GetValue(xelem, "edges", False)
        self.vertices = XH.GetValue(xelem, "vertices", False)
        self.substrate = grid.Wave(XH.GetValue(xelem, "on", ""))
        return True

    def Reset(self):
        pass

    def Go(self):
        print("Go for Node:{0}".format(self))
        frontier = [] # 边界
        start_positions = []
        generations = [-1]*len(self.grid.state)
        MX = self.grid.MX
        MY = self.grid.MY
        MZ = self.grid.MZ

        for z in range(MZ):
            for y in range(MY):
                for x in range(MX):
                    i = x + y * MX + z * MX * MY
                    generations[i] = -1
                    s = self.grid.state[i]
                    if (self.start & 1 << s) != 0:
                        start_positions.append((x,y,z))
                    if (self.finish & 1 << s) != 0:
                        generations[i] = 0
                        frontier.append((0,x,y,z))
        if len(start_positions) == 0 or len(frontier) == 0:
            return False
        
        def push(t, x, y, z):
            i = x + y * MX + z * MX * MY
            v = self.grid.state[i]
            if generations[i] == -1 and ((self.substrate & 1 << v) != 0 or (self.start & 1 << v) != 0):
                if (self.substrate & 1 << v) != 0:
                    frontier.append((t,x,y,z))
                generations[i] = t

        while len(frontier) != 0:
            (t,x,y,z) = frontier.pop(0)
            for (dx, dy, dz) in self.Directions(x, y, z, MX, MY, MZ, self.edges, self.vertices):
                push(t + 1, x + dx, y + dy, z + dz)
        
        if len(filter(lambda x : generations[x[0] + x[1] * MX + x[2] * MX * MY], start_positions)) == 0:
            return False

        local_random = rd.randrange(0, sys.maxsize)
        rd.seed(rd.randrange(0, sys.maxsize))
        min = MX * MY * MZ
        max = -2

        argmin = argmax = (-1,-1,-1)

        for p in start_positions:
            g = generations[p[0] + p[1] * MX + p[2] * MX * MY]
            if g == -1:
                continue
            dg = g
            noise = 0.1 * rd.uniform(0,1)
            if dg + noise < min:
                min = dg + noise
                argmin = p
            if dg + noise > max:
                max = dg + noise
                argmax = p

        (penx, peny, penz) = argmax if self.longest else argmin
        (dirx, diry, dirz) = self.Direction(penx, peny, penz, 0, 0, 0, generations, local_random)
        penx += dirx
        peny += diry
        penz += dirz

        while generations[penx + peny * MX + penz * MX * MY] != 0:
            self.grid.state[penx + peny * MX + penz * MX * MY] = self.value
            self.ip.changes.append((penx, peny, penz))
            (dirx, diry, dirz) = self.Direction(penx, peny, penz, dirx, diry, dirz, generations, local_random)
            penx += dirx
            peny += diry
            penz += dirz

        return True

    
    def Direction(self, x, y, z, dx, dy, dz, generations, random):
        candidates = []
        MX = self.grid.MX
        MY = self.grid.MY
        MZ = self.grid.MZ

        g = generations[x + y * MX + z * MX * MY]

        def add(DX, DY, DZ):
            if generations[x + DX + (y + DY) * MX + (z + DZ) * MX * MY] == g - 1:
                candidates.append((DX, DY, DZ))
        
        if not self.vertices and not self.edges:
            if dx != 0 or dy !=0 or dz !=0:
                cx = x + dx
                cy = y + dy
                cz = z + dz
                if self.inertia and cx >= 0 and cy >= 0 and cx < MX and cy < MY and cz < MZ and generations[cx + cy * MX + cz * MX * MY] == g - 1:
                    return (dx, dy, dz)
                if x > 0:
                    add(-1, 0, 0)
                if x < MX - 1:
                    add(1,0,0)
                if y > 0:
                    add(0,-1,0)
                if y < MY - 1:
                    add(0,1,0)
                if z > 0:
                    add(0,0,-1)
                if z < MZ - 1:
                    add(0,0,1)
                return He.RandomList(candidates, random)
        else:
            for p in PathNode.Directions(x,y,z,MX,MY,MZ,self.edges,self.vertices):
                add(p[0], p[1], p[2])
            result = (-1,-1,-1)
            if self.inertia and (dx != 0 or dy != 0 or dz != 0):
                max_scalar = -4
                for c in candidates:
                    noise = 0.1 * rd.uniform(0,1)
                    cos = (c[0] * dx + c[1] * dy + c[2] * dz) / math.sqrt((c[0]*c[0]+c[1]*c[1]+c[2]*c[2])*(dx*dx+dy*dy+dz*dz))

                    if cos + noise > max_scalar:
                        max_scalar = cos + noise
                        result = c
            else:
                result = He.RandomList(candidates, random)
            return result


    @staticmethod
    def Directions(x, y, z, MX, MY, MZ, edges, vertices):
        result = []
        if MZ == 1:
            if x > 0:
                result.append((-1,0,0))
            if x < MX - 1:
                result.append((1,0,0))
            if y > 0:
                result.append((0,-1,0))
            if y < MY - 1:
                result.append((0,1,0))

            if edges:
                if x > 0 and y > 0:
                    result.append((-1,-1,0))
                if x > 0 and y < MY - 1:
                    result.append((-1,1,0))
                if x < MX - 1 and y > 0:
                    result.append((1,-1,0))
                if x < MX - 1 and y < MY - 1:
                    result.append((1,1,0))
        else:
            if x > 0:
                result.append((-1,0,0))
            if x < MX - 1:
                result.append((1,0,0))
            if y > 0:
                result.append((0,-1,0))
            if y < MY - 1:
                result.append((0,1,0))
            if z > 0:
                result.append((0,0,-1))
            if z < MZ - 1:
                result.append((0,0,1))

            if edges:
                if x > 0 and y > 0:
                    result.append((-1,-1,0))
                if x > 0 and y < MY - 1:
                    result.append((-1,1,0))
                if x < MX - 1 and y > 0:
                    result.append((1,-1,0))
                if x < MX - 1 and y < MY - 1:
                    result.append((1,1,0))
                
                if x > 0 and z > 0:
                    result.append((-1,0,-1))
                if x > 0 and z < MZ - 1:
                    result.append((-1,0,1))
                if x < MX - 1 and z > 0:
                    result.append((1,0,-1))
                if x < MX - 1 and z < MZ - 1:
                    result.append((1,0,1))

                if y > 0 and z > 0:
                    result.append((0,-1,-1))
                if y > 0 and z < MZ - 1:
                    result.append((0,-1,1))
                if y < MY - 1 and z > 0:
                    result.append((0,1,-1))
                if y < MY - 1 and z < MZ - 1:
                    result.append((0,1,1))

            if vertices:
                if x > 0 and y > 0 and z > 0:
                    result.append((-1,-1,-1))
                if x > 0 and y > 0 and z < MZ - 1:
                    result.append((-1,-1,1))
                if x > 0 and y < MY - 1 and z > 0:
                    result.append((-1,1,-1))
                if x > 0 and y < MY - 1 and z < MZ - 1:
                    result.append((-1,1,1))
                if x < MX - 1 and y > 0 and z > 0:
                    result.append((1,-1,-1))
                if x < MX - 1 and y > 0 and z < MZ - 1:
                    result.append((1,-1,1))
                if x < MX - 1 and y < MY - 1 and z > 0:
                    result.append((1,1,-1))
                if x < MX - 1 and y < MY - 1 and z < MZ - 1:
                    result.append((1,1,1))

        return result

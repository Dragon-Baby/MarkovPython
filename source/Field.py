import XMLHelper as XH

class Field():
    def __init__(self, xelem, grid):
        self.recompute = XH.GetValue(xelem, "recompute", False)
        self.essential = XH.GetValue(xelem, "essential", False)
        self.inversed = False
        
        on = XH.GetValue(xelem, "on", "")
        self.substrate = grid.Wave(on)

        zero_symbols = XH.GetValue(xelem, "from", "")
        if zero_symbols != "":
            self.inversed = True
        else:
            zero_symbols = XH.GetValue(xelem, "to", "")
        self.zero = grid.Wave(zero_symbols)

    def Compute(self, potential, grid):
        MX = grid.MX
        MY = grid.MY
        MZ = grid.MZ
        front = []
        
        ix = iy = iz = 0
        for i in range(len(grid.state)):
            potential[i] = -1
            value = grid.state[i]
            if (self.zero & 1 << value) != 0:
                potential[i] = 0
                front.append((0,ix,iy,iz))
            ix += 1
            if ix == MX:
                ix = 0
                iy += 1
                if iy == MY:
                    iy = 0
                    iz += 1

        if len(front) == 0:
            return False
        while len(front) != 0:
            (t, x, y, z) = front.pop(0)
            neighbors = Field.Neighbours(x, y, z, MX, MY, MZ)
            for n in range(len(neighbors)):
                (nx, ny, nz) = neighbors[n]
                i = nx + ny * grid.MX + nz * grid.MX * grid.MY
                v = grid.state[i]
                if potential[i] == -1 and (self.substrate & 1 << v) != 0:
                    front.append((t + 1, nx, ny, nz))
                    potential[i] = t + 1

        return True
  
    @staticmethod
    def Neighbors(x, y, z, MX, MY, MZ):
        result = []
        if x > 0:
            result.append((x - 1, y, z))
        if x < MX - 1:
            result.append((x + 1, y, z))
        if y > 0:
            result.append((x, y - 1, z))
        if y < MY - 1:
            result.append((x, y + 1, z))
        if z > 0:
            result.append((x, y, z - 1))
        if z < MZ - 1:
            result.append((x, y, z + 1))
        return result

    @staticmethod
    def DeltaPointwise(state, rule, x, y, z, fields, potentials, MX, MY):
        sum = 0
        dz = dy = dx = 0
        for di in range(len(rule.input)):
            newvalue = rule.output[di]
            if newvalue != 0xff and (rule.input[di] & 1 << newvalue) == 0:
                i = x + dx + (y + dy) * MX + (z + dz) * MX * MY
                newpotential = potentials[newvalue][i]
                if newpotential == -1:
                    return None
                oldvalue = state[i]
                oldpotential = potentials[oldvalue][i]
                sum += newpotential - oldpotential
                if fields != []:
                    old_field = fields[oldvalue]
                    if old_field != None and old_field.inversed:
                        sum += 2 * oldpotential
                    new_field = fields[newvalue]
                    if new_field != None and new_field.inversed:
                        sum -= 2 * newpotential

            dx += 1
            if dx == rule.IMX:
                dx = 0
                dy += 1
                if dy == rule.IMY:
                    dy = 0
                    dz += 1
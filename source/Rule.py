from tkinter import X
import XMLHelper as XH
import SymmetryHelper as SH 
import Helper as He
import Graphics as Gp
import VoxHelper as VH


class Rule():
    def __init__(self, input, IMX, IMY, IMZ, output, OMX, OMY, OMZ, C, p):
        self.input = input  # list of int
        self.IMX = IMX  # int
        self.IMY = IMY  # int
        self.IMZ = IMZ  # int
        self.OMX = OMX  # int
        self.OMY = OMY  # int
        self.OMZ = OMZ  # int
        self.p = p  # float
        self.output = output    # list of byte
        self.binput = []    # list of byte
        self.ishifts = []   # list of list of (int, int, int)
        self.oshifts = []   # list of list of (int, int, int)
        self.original = False   # bol

        lists = [[] for i in range(C)]
        for z in range(self.IMZ):
            for y in range(self.IMY):
                for x in range(self.IMX):
                    w = self.input[x + y * self.IMX + z * self.IMY * self.IMX]
                    for c in range(C):
                        if (w & 1) == 1:
                            lists[c].append([x,y,z])
                        w >>= 1

        self.ishifts = lists[:]


        if self.OMX == self.IMX and self.OMY == self.IMY and self.OMZ == self.IMZ:
            for c in range(C):
                lists[c] = []
            for z in range(self.IMZ):
                for y in range(self.IMY):
                    for x in range(self.IMX):
                        # byte
                        o = self.output[x + y * self.IMX + z * self.IMY * self.IMX]
                        if o != 0xff:
                            lists[o].append([x,y,z])
                        else:
                            for c in range(C):
                                lists[c].append([x,y,z])
            self.oshifts = lists[:]

        wild_card = (1 << C) - 1
        self.binput = [0 for i in range(len(self.input))]
        for i in range(0, len(self.input)):
            w = self.input[i]
            self.binput[i] = 0xff if w == wild_card else (len(bin(w)[2:]) - len(bin(w)[2:].rstrip("0"))) * 0xff

    def ZRotated(self):
        newinput = [0 for i in range(len(self.input))]
        for z in range(self.IMZ):
            for y in range(self.IMX):
                for x in range(self.IMY):
                    newinput[x + y * self.IMY + z * self.IMX * self.IMY] = self.input[self.IMX - 1 - y + x * self.IMX + z * self.IMX * self.IMY]

        newoutput = [0 for i in range(len(self.output))]
        for z in range(self.OMZ):
            for y in range(self.OMX):
                for x in range(self.OMY):
                    newoutput[x + y * self.OMY + z * self.OMX * self.OMY] = self.output[self.OMX - 1 - y + x * self.OMX + z * self.OMX * self.OMY]
        
        return Rule(newinput, self.IMY, self.IMX, self.IMZ, newoutput, self.OMY, self.OMX, self.OMZ, len(self.ishifts), self.p)


    def YRotated(self):
        newinput = [0 for i in range(len(self.input))]
        for z in range(self.IMX):
            for y in range(self.IMY):
                for x in range(self.IMZ):
                    newinput[x + y * self.IMZ + z * self.IMZ * self.IMY] = self.input[self.IMX - 1 - z + y * self.IMX + x * self.IMX * self.IMY]

        newoutput = [0 for i in range(len(self.output))]
        for z in range(self.OMX):
            for y in range(self.OMY):
                for x in range(self.OMZ):
                    newoutput[x + y * self.OMZ + z * self.OMZ * self.OMY] = self.output[self.OMX - 1 - z + y * self.OMX + x * self.OMX * self.OMY]
        
        return Rule(newinput, self.IMY, self.IMX, self.IMZ, newoutput, self.OMY, self.OMX, self.OMZ, len(self.ishifts), self.p)

    
    def Reflected(self):
        newinput = [0 for i in range(len(self.input))]
        for z in range(self.IMZ):
            for y in range(self.IMY):
                for x in range(self.IMX):
                    newinput[x + y * self.IMX + z * self.IMX * self.IMY] = self.input[self.IMX - 1 - x + y * self.IMX + z * self.IMX * self.IMY]

        newoutput = [0 for i in range(len(self.output))]
        for z in range(self.OMZ):
            for y in range(self.OMY):
                for x in range(self.OMX):
                    newoutput[x + y * self.OMX + z * self.OMX * self.OMY] = self.output[self.OMX - 1 - x + y * self.OMX + z * self.OMX * self.OMY]
        
        return Rule(newinput, self.IMY, self.IMX, self.IMZ, newoutput, self.OMY, self.OMX, self.OMZ, len(self.ishifts), self.p)


    @staticmethod
    def Same(a1, a2):
        if a1.IMX != a2.IMX or a1.IMY != a2.IMY or a1.IMZ != a2.IMZ or a1.OMX != a2.OMX or a1.OMY != a2.OMY or a1.OMZ != a2.OMZ:
            return False
        for i in range(a1.IMX * a1.IMY * a1.IMZ):
            if a1.input[i] != a2.input[i]:
                return False
        for i in range(a1.OMX * a1.OMY * a1.OMZ):
            if a1.output[i] != a2.output[i]:
                return False
        return True
        

    def Symmetries(self, symmetry, d2):
        if d2:
            return SH.SquareSymmetries(self, lambda r : r.ZRotated(), lambda r : r.Reflected(), Rule.Same, symmetry)
        else:
            return SH.CubeSymmetries(self, lambda r : r.ZRotated(), lambda r : r.YRotated(), lambda r : r.Reflected(), Rule.Same, symmetry)

    @staticmethod
    def LoadResource(filename, legend, d2):
        if legend == "":
            print("no legend for {0}".format(filename))
            return ([], -1, -1, -1)
        
        (data, MX, MY, MZ) = Gp.LoadBitmap(filename) if d2 else VH.LoadVox(filename)

        if data == []:
            print("couldn't read {0}".format(filename))
            return ([], MX, MY, MZ)
        (ords, amount) = He.Ords(data)    ## TO-DO
        if amount > len(legend):
            print("the amount of colors {0} in {1} is more than {2}".format(amount, filename, len(legend)))
            return ([], MX, MY, MZ)
        return (list(map(lambda x : legend[x], ords)), MX, MY, MZ)

    
    @staticmethod
    def Parse(s):
        lines = He.Split(s, " ", "/")
        MX = len(lines[0][0])
        MY = len(lines[0])
        MZ = len(lines)
        result = [""]*MX*MY*MZ

        for z in range(MZ):
            linesz = lines[MZ - 1 - z]
            if len(linesz) != MY:
                print("non-rectangular pattern")
                return ([], -1, -1, -1)
            for y in range(MY):
                lineszy = linesz[y]
                if len(lineszy) != MX:
                    print("non-rectangular pattern")
                    return ([], -1, -1, -1)
                for x in range(MX):
                    result[x + y * MX + z * MX * MY] = lineszy[x]

        return (result, MX, MY, MZ)
        
    
    @staticmethod
    def Load(xelem, gin, gout):
        line_number = xelem._start_line_number

        import os 
        src_folder = "{0}".format(os.path.dirname(os.path.abspath(__file__)).rstrip("\source"))


        def file_path(name):
            result = "{0}/resources/rules/".format(src_folder)
            if gout.folder != "":
                result += gout.folder + "/"
            result += name
            result += ".png" if gin.MZ == 1 else ".vox"
            return result
        
        in_str = XH.GetValue(xelem, "in", "")
        print("[Rule] > IN :", in_str)
        out_str = XH.GetValue(xelem, "out", "")
        print("[Rule] > OUT:", out_str)
        fin_str = XH.GetValue(xelem, "fin", "")
        fout_str = XH.GetValue(xelem, "fout", "")
        file_str = XH.GetValue(xelem, "file", "")
        legend = XH.GetValue(xelem, "legend", "")

        in_rect = []
        out_rect = []
        IMX = IMY = IMZ = OMX = OMY = OMZ = -1
        if file_str == "":
            if in_str == "" and fin_str == "":
                print("[Rule] > !!! no input in a rule at line {0}".format(line_number))
                return None
            if out_str == "" and fout_str == "":
                print("[Rule] > !!! no output in a rule at line {0}".format(line_number))
                return None
            
            (in_rect, IMX, IMY, IMZ) = Rule.Parse(in_str) if in_str != "" else Rule.LoadResource(file_path(fin_str), legend, gin.MZ==1)
            if in_rect == []:
                print(" in input at line {0}".format(line_number))
                return None

            (out_rect, OMX, OMY, OMZ) = Rule.Parse(out_str) if out_str != "" else Rule.LoadResource(file_path(fout_str), legend, gin.MZ==1)
            if out_rect == []:
                print(" in output at line {0}".format(line_number))
                return None

            if gin == gout and (OMZ != IMZ or OMY != IMY or OMX != IMX):
                print("[Rule] > !!! non-matching pattern sizes at line {0}".format(line_number))
                return None
        else:
            if in_str != "" or fin_str != "" or out_str != "" or fout_str != "":
                print("[Rule] > !!! rule at line {0} already contains a file attribute".format(line_number))
                return None
            (rect, FX, FY, FZ) = Rule.LoadResource(file_path(file_str), legend, gin.MZ==1)
            if rect == []:
                print(" in a rule at line {0}".format(line_number))
                return None
            if FX % 2 != 0:
                print("[Rule] > !!! odd width {0} in {1}".format(FX, file_str))
                return None

            IMX = OMX = int(FX / 2)
            IMY = OMY = FY
            IMZ = OMZ = FZ

            for z in range(FZ):
                for y in range(FY):
                    for x in range(int(FX / 2)):
                        in_rect = rect[x + y * FX + z * FX * FY]
                        out_rect = rect[x + int(FX / 2) + y * FX + z * FX * FY]

        input = [0 for i in range(len(in_rect))]
        for i in range(len(in_rect)):
            c = in_rect[i]
            value = 0
            if c in gin.waves.keys():
                value = gin.waves[c]
            else:
                print("[Rule] > !!! input code {0} at line {1} is not found in codes".format(c, line_number))
                return None
            input[i] = value
        

        output = [0 for i in range(len(out_rect))]
        for i in range(len(out_rect)):
            c = out_rect[i]
            if c == "*":
                output[i] = 0xff
            else:
                value = 0
                if c in gout.values.keys():
                    value = gout.values[c]
                else:
                    print("[Rule] > !!! output code {0} at line {1} is not found in codes".format(c, line_number))
                    return None
                output[i] = value  

        print("[Rule] > Input :", input)
        print("[Rule] > Output :", output)

        p = XH.GetValue(xelem, "p", 1.0)
        rule = Rule(input, IMX, IMY, IMZ, output, OMX, OMY, OMZ, gin.C, p)
        return rule


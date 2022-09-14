squareSubgroups = {
    "()" : [True, False, False, False, False, False, False, False],
    "(x)": [True, True, False, False, False, False, False, False],
    "(y)": [True, False, False, False, False, True, False, False],
    "(x)(y)" : [True, True, False, False, True, True, False, False],
    "(xy+)": [True, False, True, False, True, False, True, False],
    "(xy)": [True, True, True, True, True, True, True, True]
}

cubeSubgroups = {
    "()" : list(map(lambda x : x == 0, list(range(48)))),
    "(x)" : list(map(lambda x : x == 0 or x == 1, list(range(48)))),
    "(z)" : list(map(lambda x : x == 0 or x == 17, list(range(48)))),
    "(xy)" : list(map(lambda x : x < 8, list(range(48)))),
    "(xyz+)" : list(map(lambda x : x % 2 == 0, list(range(48)))),
    "(xyz)" : [True for i in range(48)]
}

def GetSymmetry(d2, s, dflt):
    if s == "":
        return dflt
    result = []
    success = False
    if s in squareSubgroups.keys():
        result = squareSubgroups[s]
        success = d2
    if not success:
        if s in cubeSubgroups.keys():
            result = cubeSubgroups[s]
            success = True
        else:
            success = False

    if success:
        return result
    else:
        return []

def SquareSymmetries(thing, rotation, reflection, same, subgroup=[]):
    things = [None for i in range(8)]
    things[0] = thing
    things[1] = reflection(things[0])  # b
    things[2] = rotation(things[0])    # a
    things[3] = reflection(things[2])  # ba
    things[4] = rotation(things[2])    # a2
    things[5] = reflection(things[4])  # ba2
    things[6] = rotation(things[4])    # a3
    things[7] = reflection(things[6])  # ba3

    result = []
    for i in range(8):
        if (subgroup == [] or subgroup[i]) and len(list(filter(lambda x : same(x, things[i]), result))) == 0:
            result.append(things[i])

    return result

def CubeSymmetries(thing, a, b, r, same, subgroup=[]):
    s = [None for i in range(48)]
    s[0] = thing
    s[1] = r(s[0])
    s[2] = a(s[0])      # a
    s[3] = r(s[2])
    s[4] = a(s[2])      # a2
    s[5] = r(s[4])
    s[6] = a(s[4])      # a3
    s[7] = r(s[6])
    s[8] = b(s[0])      # b
    s[9] = r(s[8])
    s[10] = b(s[2])     # b a
    s[11] = r(s[10])
    s[12] = b(s[4])     # b a2
    s[13] = r(s[12])
    s[14] = b(s[6])     # b a3
    s[15] = r(s[14])
    s[16] = b(s[8])     # b2
    s[17] = r(s[16])
    s[18] = b(s[10])    # b2 a
    s[19] = r(s[18])
    s[20] = b(s[12])    # b2 a2
    s[21] = r(s[20])
    s[22] = b(s[14])    # b2 a3
    s[23] = r(s[22])
    s[24] = b(s[16])    # b3
    s[25] = r(s[24])
    s[26] = b(s[18])    # b3 a
    s[27] = r(s[26])
    s[28] = b(s[20])    # b3 a2
    s[29] = r(s[28])
    s[30] = b(s[22])    # b3 a3
    s[31] = r(s[30])
    s[32] = a(s[8])     # a b
    s[33] = r(s[32])
    s[34] = a(s[10])    # a b a
    s[35] = r(s[34])
    s[36] = a(s[12])    # a b a2
    s[37] = r(s[36])
    s[38] = a(s[14])    # a b a3
    s[39] = r(s[38])
    s[40] = a(s[24])    # a3 b a2 = a b3
    s[41] = r(s[40])
    s[42] = a(s[26])    # a3 b a3 = a b3 a
    s[43] = r(s[42])
    s[44] = a(s[28])    # a3 b = a b3 a2
    s[45] = r(s[44])
    s[46] = a(s[30])    # a3 b a = a b3 a3
    s[47] = r(s[46])  

    result = []
    for i in range(48):
        if (subgroup == [] or subgroup[i]) and len(list(filter(lambda x : same(x, s[i]), result))) == 0:
            result.append(s[i])

    return result
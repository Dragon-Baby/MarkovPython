import struct

def LoadVox(filename):
    result = []
    MX = MY = MZ = -1
    with open(filename, mode='rb') as file:
        file_content = file.read()
        length = len(file_content)

        pos = 0
        magic = struct.unpack("BBBB", file_content[pos:pos+4])
        # print(type(magic[0]))
        pos += 4
        magic = ''.join(list(map(lambda x : chr(x), magic)))
        print("magic : {0}".format(magic))

        version = struct.unpack("i", file_content[pos:pos+4])
        pos += 4
        version = version[0]
        print("version : {0}".format(version))

        while pos < length:
            bt = struct.unpack("B", file_content[pos:pos+1])[0]
            pos += 1
            # print(bt)
            head = chr(bt)
            
            if head == 'S':
                tail = struct.unpack("BBB", file_content[pos:pos+3])
                pos += 3
                tail = ''.join(list(map(lambda x : chr(x), tail)))
                if tail != "IZE":
                    continue

                chunk_size = struct.unpack("i", file_content[pos:pos+4])
                pos += 4
                chunk_size = chunk_size[0]
                # blank
                pos += 4

                MX = struct.unpack("i", file_content[pos:pos+4])
                pos += 4
                MX = MX[0]
                MY = struct.unpack("i", file_content[pos:pos+4])
                pos += 4
                MY = MY[0]
                MZ = struct.unpack("i", file_content[pos:pos+4])
                pos += 4
                MZ = MZ[0]
                # blank
                pos += (chunk_size - 4 * 3)

            elif head == 'X':
                tail = struct.unpack("BBB", file_content[pos:pos+3])
                pos += 3
                tail = ''.join(list(map(lambda x : chr(x), tail)))
                if tail != "YZI":
                    continue

                if MX <= 0 or MY <= 0 or MY <= 0:
                    return ([], MX, MY, MZ)
                result = [-1 for i in range(MX * MY * MZ)]
                
                # blank
                pos += 8
                num_voxels = struct.unpack("i", file_content[pos:pos+4])
                pos += 4
                num_voxels = num_voxels[0]

                for i in range(num_voxels):
                    x = struct.unpack("B", file_content[pos:pos+1])[0]
                    pos += 1
                    y = struct.unpack("B", file_content[pos:pos+1])[0]
                    pos += 1
                    z = struct.unpack("B", file_content[pos:pos+1])[0]
                    pos += 1
                    color = struct.unpack("B", file_content[pos:pos+1])[0]
                    pos += 1
                    # print(x,y,z,chr(color))
                    result[x + y * MX + z * MX * MY] = color

        return result, MX, MY, MZ

def SaveVox(state, MX, MY, MZ, palette, filename):
    voxels = []
    for z in range(MZ):
        for y in range(MY):
            for x in range(MX):
                i = x + y * MX + z * MX * MY
                v = state[i]
                if v != 0:
                    voxels.append((x, y, z, v + 1))
    
    with open(filename, 'wb+') as file:
        file.write(bytes("VOX "))
        file.write(bytes(150))

        file.write(bytes("MAIN"))
        file.write(bytes(0))
        file.write(bytes(1092 + 4 * len(voxels)))

        file.write(bytes("PACK"))
        file.write(bytes(4))
        file.write(bytes(0))
        file.write(bytes(1))

        file.write(bytes("SIZE"))
        file.write(bytes(12))
        file.write(bytes(0))
        file.write(bytes(int(MX)))
        file.write(bytes(int(MY)))
        file.write(bytes(int(MZ)))
        
        file.write(bytes("XYZI"))
        file.write(bytes(4 + 4 * len(voxels)))
        file.write(bytes(0))
        file.write(bytes(len(voxels)))

        for (x, y, z, color) in voxels:
            file.write(bytes(x))
            file.write(bytes(y))
            file.write(bytes(z))
            file.write(bytes(color))

        file.write(bytes("RGBA"))
        file.write(bytes(1024))
        file.write(bytes(0))

        for c in range(palette):
            file.write(bytes((c & 0xff0000) >> 16))
            file.write(bytes((c & 0xff00) >> 8))
            file.write(bytes(c & 0xff))
            file.write(bytes(0))

        for i in range(len(palette), 255):
            file.write(bytes(0xff - i - 1))
            file.write(bytes(0xff - i- 1))
            file.write(bytes(0xff - i- 1))
            file.write(bytes(0xff))

        file.write(bytes(0))
        
        
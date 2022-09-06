from PIL import Image

sprites = {}

def LoadBitmap(filename):
    try:
        image = Image.open(filename)
        width = image.width
        height = image.height
        result = list(image.getdata())
        return (result, width, height, 1)
    except:
        return ([], -1, -1, -1)


def SaveBitmap(data, width, height, filename):
    if width <= 0 or height <= 0 or len(data) != width * height:
        print("ERROR: wrong image width * height = {0} * {1}".format(width, height))
        return

    image = Image.fromarray(data)
    image.save(filename)


# def BitmapRender(state, MX, MY, colors, pixelsize, MARGIN):
#     pass

# def IsometricRender(state, MX, MY, MZ, colors, pixelsize, MARGIN):
#     pass


# def Render(state, MX, MY, MZ, colors, pixelsize, MARGIN):
#     if MZ == 1:
#         return BitmapRender(state, MX, MY, colors, pixelsize, MARGIN)
#     else:
#         return IsometricRender(state, MX, MY, MZ, colors, pixelsize, MARGIN)



class Sprite():
    c1 = 215
    c2 = 143
    c3 = 71
    black = 0
    transparent = -1

    def __init__(self, size):
        self.width = 2 * size
        self.height = 2 * size - 1

        def texture(f):
            result = [0] * self.width * self.height
            for j in range(self.height):
                for i in range(self.width):
                    result[i + j * self.width] = f(i - size + 1, size - j - 1)
            return result

        def f(x, y):
            if 2 * y - x >= 2 * size or 2 * y + x > 2 * size or 2 * y - x < -2 * size or 2 * y + x <= -2 * size:
                return Sprite.transparent
            elif x > 0 and 2 * y < x:
                return Sprite.c3
            elif x <= 0 and 2 * y <= -x:
                return Sprite.c2
            else:
                return Sprite.c1

        self.cube = texture(f)
        self.edges = [[]] * 8
        self.edges[0] = texture(lambda x, y : Sprite.c1 if x == 1 and y <= 0 else Sprite.transparent)
        self.edges[1] = texture(lambda x, y : Sprite.c1 if x == 0 and y <= 0 else Sprite.transparent)
        self.edges[2] = texture(lambda x, y : Sprite.black if x == 1 - size and 2 * y < size and 2 * y >= -size else Sprite.transparent)
        self.edges[3] = texture(lambda x, y : Sprite.black if x <= 0 and y == x / 2 + size - 1 else Sprite.transparent)
        self.edges[4] = texture(lambda x, y : Sprite.black if x == size and 2 * y < size and 2 * y >= -size else Sprite.transparent)
        self.edges[5] = texture(lambda x, y : Sprite.black if x > 0 and y == -(x + 1) / 2 + size else Sprite.transparent)
        self.edges[6] = texture(lambda x, y : Sprite.black if x > 0 and y == (x + 1) / 2 - size else Sprite.transparent)
        self.edges[7] = texture(lambda x, y : Sprite.black if x <= 0 and y == -x / 2 - size + 1 else Sprite.transparent)




class Voxel():
    def __init__(self, color, x, y, z):
        self.color = color
        self.x = x
        self.y = y
        self.z = z
        self.edges = [False] * 8
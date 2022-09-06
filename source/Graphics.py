from PIL import Image

def LoadBitmap(filename):
    try:
        image = Image.open(filename)
        width = image.width
        height = image.height
        result = list(image.getdata())
        return (result, width, height, 1)
    except:
        return ([], -1, -1, -1)
import XMLHelper as XH
import xml.etree.ElementTree as ET
import os 
import sys
import pathlib
import random as rd
from Interpreter import Interpreter


if __name__ == "__main__":
    src_folder = pathlib.Path().resolve()
    # print(src_folder)

    # create output folder
    folder = os.path.join(src_folder, "output")
    if not os.path.exists(folder):
        os.mkdir(folder)
    else:
        file_list = os.listdir(folder)
        for file in file_list:
            os.remove(file)

    # color
    palette_xml = ET.parse("resources/palette.xml")
    palette = {}
    for e in palette_xml.getroot().findall("./color"):
        symbol = XH.GetValue(e, "symbol", "")
        value = int(XH.GetValue(e, "value", ""), 16) + 255 << 24
        palette[symbol] = value

    # model 
    xdoc = ET.parse("models.xml", parser=XH.LineNumberingParser())
    for xmodel in xdoc.getroot().findall("./model"):
        name = XH.GetValue(xmodel, "name", "")
        linear_size = XH.GetValue(xmodel, "size", -1)
        dimension = XH.GetValue(xmodel, "d", 2)
        MX = XH.GetValue(xmodel, "length", linear_size)
        MY = XH.GetValue(xmodel, "width", linear_size)
        MZ = XH.GetValue(xmodel, "height", 1 if dimension == 2 else linear_size)

        print("{0} > ".format(name))
        file_name = "models/{0}.xml".format(name)
        model_doc = None
        try:
            model_doc = ET.parse(file_name, parser=XH.LineNumberingParser())
        except:
            print("ERROR: couldn't open xml file {0}".format(file_name))
            continue

        # model interpreter
        interpreter = Interpreter.Load(model_doc.getroot(), MX, MY, MZ)
        if interpreter == None:
            print("ERROR")
            continue

        amount = XH.GetValue(xmodel, "amount", 2)
        pixel_size = XH.GetValue(xmodel, "pixelsize", 4)
        seed_str = XH.GetValue(xmodel, "seeds", "")
        seeds = list(map(lambda x : int(x), seed_str.split(" "))) if seed_str != "" else []
        gif = XH.GetValue(xmodel, "gif", False)
        iso = XH.GetValue(xmodel, "iso", False)
        steps = XH.GetValue(xmodel, "steps", 1000 if gif else 50000)
        gui = XH.GetValue(xmodel, "gui", 0)
        if gif:
            amount = 1
        
        custom_palette = {}
        for x in xmodel.findall("./color"):
            custom_palette[XH.GetValue(x, "symbol", "")] = int(XH.GetValue(x, "value", ""), 16) + 255 << 24

        for k in range(amount):
            seed = seeds[k] if seeds != [] and k < len(seeds) else rd.randrange(0, sys.maxsize)
            # interpreter run
            for result, legend, FX, FY, FZ in iter(interpreter.Run(seed, steps, gif)):
                colors = list(map(lambda x : custom_palette[x], legend))
                output_name = "output/{0}".format(interpreter.counter) if gif else "output/{0}_{1}".format(name, seed)
                #### Render in Houdini
                if FZ == 1 or iso:
                    # draw pic or vox
                    pass
                else:
                    # save vox
                    pass
            print("DONE")
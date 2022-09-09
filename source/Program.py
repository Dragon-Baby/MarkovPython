import sys, os
sys.modules['_elementtree'] = None
import XMLHelper as XH
import xml.etree.ElementTree as ET
import random as rd
import Interpreter

def main():
    src_folder = "{0}".format(os.path.dirname(os.path.abspath(__file__)).rstrip("\source"))
    # src_folder = "{0}".format(os.path.dirname(hou.hipFile.path()))
    print(src_folder)

    # create output folder
    folder = os.path.join(src_folder, "output")
    if not os.path.exists(folder):
        os.mkdir(folder)
    else:
        file_list = os.listdir(folder)
        for file in file_list:
            os.remove(file)

    # color
    palette_xml = ET.parse("{0}/resources/palette.xml".format(src_folder))
    palette = {}
    for e in palette_xml.getroot().findall("./color"):
        symbol = XH.GetValue(e, "symbol", "")
        # print(symbol)
        value = int(XH.GetValue(e, "value", ""), 16)
        palette[symbol] = value

    # print(palette)

    # model 
    xdoc = ET.parse("{0}/models.xml".format(src_folder), parser=XH.LineNumberingParser())
    for xmodel in xdoc.getroot().findall("./model"):
        name = XH.GetValue(xmodel, "name", "")
        linear_size = XH.GetValue(xmodel, "size", -1)
        dimension = XH.GetValue(xmodel, "d", 2)
        MX = XH.GetValue(xmodel, "length", linear_size)
        MY = XH.GetValue(xmodel, "width", linear_size)
        MZ = XH.GetValue(xmodel, "height", 1 if dimension == 2 else linear_size)

        print("{0} > ".format(name))
        file_name = "{0}/models/{1}.xml".format(src_folder, name)
        print(file_name)
        model_doc = None
        model_doc = ET.parse(file_name, parser=XH.LineNumberingParser())
        # try:
        #     model_doc = ET.parse(file_name, parser=XH.LineNumberingParser())
        # except:
        #     print("ERROR: couldn't open xml file {0}".format(file_name))
        #     continue
        print(model_doc, MX, MY, MZ)

        # model interpreter
        interpreter = Interpreter.Interpreter.Load(model_doc.getroot(), MX, MY, MZ)
        if interpreter == None:
            print("ERROR Oops")
            continue

        amount = XH.GetValue(xmodel, "amount", 1)
        pixel_size = XH.GetValue(xmodel, "pixelsize", 4)
        seed_str = XH.GetValue(xmodel, "seeds", "")
        seeds = list(map(lambda x : int(x), seed_str.split(" "))) if seed_str != "" else []
        gif = XH.GetValue(xmodel, "gif", False)
        iso = XH.GetValue(xmodel, "iso", False)
        steps = XH.GetValue(xmodel, "steps", 1000 if gif else 50000)
        gui = XH.GetValue(xmodel, "gui", 0)
        if gif:
            amount = 1
        
        custom_palette = palette
        for x in xmodel.findall("./color"):
            custom_palette[XH.GetValue(x, "symbol", "")] = int(XH.GetValue(x, "value", ""), 16) + 255 << 24

        # print(custom_palette)

        # import hou

        # node = hou.pwd()
        # geo = node.geometry()
        for k in range(amount):
            seed = seeds[k] if seeds != [] and k < len(seeds) else rd.randrange(0, sys.maxsize)
            # interpreter run
            for result, legend, FX, FY, FZ in iter(interpreter.Run(seed, steps, gif)):
                colors = list(map(lambda x : custom_palette[x], legend))
                print(colors)
                print(result)
                # pt = geo.createPoint()
                # pt.setAttribValue("state", result)
                # pt.setAttribValue("colors", colors)
                # pt.setAttribValue("FX", FX)
                # pt.setAttribValue("FY", FY)
                # pt.setAttribValue("FZ", FZ)
                # pt.setAttribValue("pixelSize", pixel_size)
                # output_name = "output/{0}".format(interpreter.counter) if gif else "output/{0}_{1}".format(name, seed)
                #### Render in Houdini
                if FZ == 1 or iso:
                    # draw pic or vox
                    pass
                else:
                    # save vox
                    pass
                yield (result, legend, FX, FY, FZ, pixel_size)
            print("DONE")



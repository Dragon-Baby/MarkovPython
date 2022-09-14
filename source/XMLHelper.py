import sys
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

class LineNumberingParser(ET.XMLParser):
    def _start(self, *args, **kwargs):
        # Here we assume the default XML parser which is expat
        # and copy its element position attributes into output Elements
        element = super(self.__class__, self)._start(*args, **kwargs)
        element._start_line_number = self.parser.CurrentLineNumber
        element._start_column_number = self.parser.CurrentColumnNumber
        element._start_byte_index = self.parser.CurrentByteIndex
        return element

    def _end(self, *args, **kwargs):
        element = super(self.__class__, self)._end(*args, **kwargs)
        element._end_line_number = self.parser.CurrentLineNumber
        element._end_column_number = self.parser.CurrentColumnNumber
        element._end_byte_index = self.parser.CurrentByteIndex
        return element

def GetValue(xelem, name, default):
    attr = xelem.attrib
    value = default
    if name in attr.keys():
        value = attr[name]
        typ = type(default)
        if typ == int:
            value = int(value)
        elif typ == float:
            value = float(value)
        elif typ == str:
            value = str(value)
        elif typ == bool:
            value = bool(value)
        else:
            print("Unknown value type")
    return value

def Elements(xelem, tags):
    children = xelem.findall("./*")
    children = list(filter(lambda e : e.tag in tags, list(children)))
    return children


def MyDescendants(xelem, tags):
    q = []
    q.append(xelem)
    while len(q) != 0:
        e = q.pop(0)
        if e != xelem:
            yield e
        for x in Elements(e, tags):
            q.append(x)
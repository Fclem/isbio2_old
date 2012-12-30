# from xml.dom import minidom
# import urllib2
import xml.etree.ElementTree as xml

tree = xml.parse('/home/comrade/Projects/fimm/isbio/breeze/templates/xml/fullExample.xml')
root = tree.getroot()

print tree.getroot().attrib['name']


input_array = tree.getroot().find('inputArray')

for input_item in input_array:
    if (input_item.tag == "inputItem") and (input_item.attrib["type"] == "textar"):
        print input_item.find('nrows').attrib['val']

"""
dom = minidom.parse('/home/comrade/Projects/fimm/isbio/breeze/templates/xml/fullExample.xml')

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


x = dom.childNodes[0].getElementsByTagName("inputItem")[3]

opt = tuple()





alt = x.childNodes
for i in alt:
    k = i.childNodes
    for j in k:
        if len(getText(j.childNodes)) == 0 :
            pass
        else:
            print getText(j.childNodes).encode('ascii', 'ignore')
f = "some str"
print f """


# node = dom.getElementsByTagName("inline")[0]
#    script_inline = getText(node.childNodes)

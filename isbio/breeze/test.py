from xml.dom import minidom

dom = minidom.parse('/home/comrade/Projects/fimm/isbio/breeze/templates/xml/fullExample.xml')

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


node = dom.getElementsByTagName("inline")[0]

print getText(node.childNodes)

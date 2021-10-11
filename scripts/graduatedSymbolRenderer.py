from qgis.PyQt import QtGui

fn = 'C:/Users/helen/Documents/Assignment5/datasets/joinSample.shp'
#iface.addVectorLayer(fn, 'name', 'ogr')

myLayer = QgsVectorLayer(fn, 'name', 'ogr')
tf = 'distance'
rangeList = []
opacity = 1

# symbology for 0-1000
minval = 0.0
maxval = 1000.0
myLabel = 'Within 1000m'
color1a = QtGui.QColor("#333333")

symbol = QgsSymbol.defaultSymbol(myLayer.geometryType())
symbol.setColor(color1a)
symbol.setOpacity(opacity)

range1a = QgsRendererRange(minval, maxval, symbol, myLabel)
rangeList.append(range1a)


# symbology for 1000+
minval1b = 1000.0
maxval1b = 10000.0
myLabel = 'Beyond 1000m'
color1b = QtGui.QColor("#eeeeee")

symbol = QgsSymbol.defaultSymbol(myLayer.geometryType())
symbol.setColor(color1b)
symbol.setOpacity(opacity)

range1b = QgsRendererRange(minval1b, maxval1b, symbol, myLabel)
rangeList.append(range1b)
print(rangeList)

# Apply ranges to layer
groupRenderer = QgsGraduatedSymbolRenderer('', rangeList)
groupRenderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
groupRenderer.setClassAttribute(tf)

myLayer.setRenderer(groupRenderer)

QgsProject.instance().addMapLayer(myLayer)
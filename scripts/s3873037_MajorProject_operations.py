###########################
#       ASSIGNMENT 5      #
#      MAJOR PROJECT      #
###########################

# import statements
import processing
#import math
from qgis.PyQt import QtGui


# Create variables.
# These will be updated for the tool to reflect files and variables 
# selected by the user in the tool UI. 

# Set user-adjustable variables
stationThreshold = 1000
toiletsThreshold = 200
hillsRating = 6
parklandThreshold = 15

# Set filepaths
inputFP = 'C:/Users/helen/Documents/Assignment5/inputData/'
outputFP = 'C:/Users/helen/Documents/Assignment5/outputData/'
sourceFP = 'C:/Users/helen/Documents/Assignment5/sourceData/'

# Add OV input layers to the map
compAreasLayer = iface.addVectorLayer((inputFP + 'compAreas_OV.shp'), 'Layer', 'ogr')
startLocationsLayer = iface.addVectorLayer((inputFP + 'startLocations_OV.shp'), 'Layer', 'ogr')

# Conduct suitability analysis on start locations. 
# Establish a list of operations to guide our loop. 
operationsList = ['nearTrainStations', 'nearEdgeOfArea', 'nearToilets', 'nearTaps', 'nearPlaygrounds']

# Derive a new layer of competiton area boundaries from the 
# compAreas polygon layer for use in the 'nearEdgeOfArea' operation. 
paramDict = {'INPUT' : (inputFP + 'compAreas_OV.shp'), 'OUTPUT':(outputFP + 'compOutlines.shp')}
processing.run('native:polygonstolines', paramDict)
compOutlinesLayer = iface.addVectorLayer((outputFP + 'compOutlines.shp'), 'Layer', 'ogr')

# 
paramDict = { 'DISCARD_NONMATCHING' : False, 'FIELDS_TO_COPY' : ['STOP_NAME'], 'INPUT' : (inputFP + 'StartLocations_OV.shp'), 'INPUT_2' : (sourceFP + 'stations_PTV.shp'), 'MAX_DISTANCE' : None, 'NEIGHBORS' : 1, 'OUTPUT' : (outputFP + 'join4_Stations.shp'), 'PREFIX' : 'STATION' }
processing.run('native:joinbynearest', paramDict)
# Create a pointer to the new layer
newLayer = QgsVectorLayer((outputFP + 'join4_Stations.shp'), 'Join4', 'ogr')

# Remove extra columns from new layer created by 'joinbynearest' operation 
#paramDict = { 'COLUMN' : ['feature_x','feature_y','nearest_x','nearest_y'], 'INPUT' : (outputFP + 'join1_Stations.shp'), 'OUTPUT' : (outputFP + 'join1_Clean.shp') }
#processing.run('native:deletecolumn', paramDict)

newLayer.dataProvider().deleteAttributes([12])
newLayer.updateFields()

paramDict = {}
processing.run('native:joinbynearest', paramDict)




for field in newLayer.fields():
    print(field.index())



#for alg in QgsApplication.processingRegistry().algorithms():
#    if "field" in alg.displayName():
#        print(alg.id(), "-->", alg.displayName())
#        
#processing.algorithmHelp("native:deletecolumn")




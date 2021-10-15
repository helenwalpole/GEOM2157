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
sourceFP = 'C:/Users/helen/Documents/Assignment5/sourceData/'
processingFP = 'C:/Users/helen/Documents/Assignment5/outputData/'

# Add OV input layers to the map
compAreasLayer = iface.addVectorLayer((inputFP + 'compAreas_OV.shp'), 'Layer', 'ogr')
startLocationsLayer = iface.addVectorLayer((inputFP + 'startLocations_OV.shp'), 'Layer', 'ogr')

# Conduct suitability analysis on start locations. 
# Establish a list of operations to guide our loop. 
#operationsList = ['nearTrainStations', 'nearEdgeOfArea', 'nearToilets', 'nearTaps', 'nearPlaygrounds']

# Derive a new layer of competiton area boundaries from the 
# compAreas polygon layer for use in the 'nearEdgeOfArea' operation. 
paramDict = {
    'INPUT' : (inputFP + 'compAreas_OV.shp'), 
    'OUTPUT': (sourceFP + 'boundaries.shp')
    }
processing.run('native:polygonstolines', paramDict)
compOutlinesLayer = iface.addVectorLayer((sourceFP + 'boundaries.shp'), 'Layer', 'ogr')

# We will calcuate distance of each start location from various features using 'joinbynearest'. 
# We will loop this operation five times for the different types of features. 
layersList = ['stations', 'boundaries', 'toilets', 'drinkTaps', 'playgrounds']

for layerIndex, layerString in enumerate(layersList):
    # Set the input filepath for the first iteration to take the file from the 'inputFP' folder. 
    # After that, take files from the processing folder
    #print(layerIndex, layerString)
    if layerIndex == 0: 
        inputParam = (inputFP + 'startLocations_OV.shp')
    else: 
        inputParam = (processingFP + 'startLocations' + str(layerIndex) + '.shp')
    #print(type(inputParam))
    
    # Create a dictionary of parameters for the algorithm specific to each item in the loop.
    paramDict = { 
    'DISCARD_NONMATCHING' : False, 
    'FIELDS_TO_COPY' : ['FID'], #all layers have this field 
    'INPUT' : inputParam, #except for first iteration, this takes the output layer from the previous loop as input
    'INPUT_2' : (sourceFP + layerString + '.shp'), #takes the correct join layer for this iteration
    'MAX_DISTANCE' : None, 
    'NEIGHBORS' : 1, 
    'OUTPUT' : (processingFP + layerString + 'Join.shp'), 
    'PREFIX' : layerString[0:5].upper() + '_'
    }
    print(paramDict)
    # Run the joinbynearest algorithm using the new dictionary
    processing.run('native:joinbynearest', paramDict)
    
    # The joinbynearest algorithm adds new fields by default that we do not need. 
    # To avoid confusion, we will remove these extra fields as we go. 
    paramDict = { 
        'COLUMN' : ['feature_x','feature_y','nearest_x','nearest_y'], 
        'INPUT' : (processingFP + layerString + 'Join.shp'), 
        'OUTPUT' : (processingFP + 'startLocations' + str(layerIndex + 1) + '.shp') 
        }
    processing.run('native:deletecolumn', paramDict)
       
# Create a pointer to the final layer
startLocationsProcessed = iface.addVectorLayer((processingFP + 'startLocations' + str(len(layersList)) + '.shp'), 'startLocations', 'ogr')

# Create two dictionaries that match the suitability criteria for start locations 
# to their threshold values and to their weights, using the data input by the user.

thresholdDict = {}
weightDict = {}

for 


#for alg in QgsApplication.processingRegistry().algorithms():
#    if "field" in alg.displayName():
#        print(alg.id(), "-->", alg.displayName())
#        
#processing.algorithmHelp("native:deletecolumn")




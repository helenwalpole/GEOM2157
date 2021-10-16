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
hillsWeight = 6
parklandThreshold = 15

# Set the fixed variables
freewayThreshold = 200
riverThreshold = True


# Set filepaths
inputFP = 'C:/Users/helen/Documents/Assignment5/inputData/'
sourceFP = 'C:/Users/helen/Documents/Assignment5/sourceData/'
processingFP = 'C:/Users/helen/Documents/Assignment5/OPTDATA2/'

# Create two dictionaries from the user input to guide suitability criteria thresholds and weights.
thresholdsDict['stations'] = stationThreshold
weightsDict['stations'] = 

thresholdsDict['toilets'] = toiletsThreshold
weightsDict['toilets'] = 

thresholdsDict['drinkTaps'] = 
weightsDict['drinkTaps'] = 

thresholdsDict['playgrounds'] = 
weightsDict['playgrounds'] = 

thresholdsDict['recentUse'] = 
weightsDict['recentUse'] = 
    
thresholdsDict['hills'] = hillsThreshold
weightsDict['hills'] = 

thresholdsDict['parkland'] = 
weightsDict['parkland'] = 


# Create pointers to the input layers 
compAreasLayer = iface.addVectorLayer((inputFP + 'compAreas_OV.shp'), 'Layer', 'ogr')
startLocationsLayer = iface.addVectorLayer((inputFP + 'startLocations_OV.shp'), 'Layer', 'ogr')

# PREPARE DATA LAYERS
# Derive a new layer of competiton area boundaries from the compAreas polygon layer for later use. 
paramDict = {
    'INPUT' : (inputFP + 'compAreas_OV.shp'), 
    'OUTPUT': (sourceFP + 'boundaries.shp')
    }
processing.run('native:polygonstolines', paramDict)
#compOutlinesLayer = iface.addVectorLayer((sourceFP + 'boundaries.shp'), 'Layer', 'ogr')


# SUITABILITY ANALYSIS: START LOCATIONS
# We will calcuate distance of each start location from various features using 'joinbynearest'. 
# We will loop this operation for each of the different types of features we are measuring. 

###########
layersList = ['stations', 'toilets', 'drinkTaps', 'playgrounds']
processingFP = 'C:/Users/helen/Documents/Assignment5/OPTDATA2/'

for layerIndex, layerString in enumerate(layersList):
    # Set the input filepath for the first iteration to take the file from the 'inputFP' folder. 
    # After that, take files from the processing folder
    print(layerIndex, layerString)
    if layerIndex == 0: 
        inputParam = (inputFP + 'startLocations_OV.shp')
    else: 
        inputParam = (processingFP + 'startLocationsCrit' + str(layerIndex) + '.shp')
    
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
    # To avoid issues arising from successive iterations overwriting these fields,
    # we will remove these extra fields as we go. 
    paramDict = { 
        'COLUMN' : ['feature_x','feature_y','nearest_x','nearest_y', 'n', (layerString[0:5].upper() + '_' + 'FID')], 
        'INPUT' : (processingFP + layerString + 'Join.shp'), 
        'OUTPUT' : (processingFP + 'startLocationsCrit' + str(layerIndex + 1) + '.shp') 
        }
    processing.run('native:deletecolumn', paramDict)
    
    # The joinbynearest algorithm has created a new field called 'distance'. 
    # We need to rename this field to keep track of which feature the distance relates to. 
    # First, create a pointer to the new layer we have created
    joinedLayer = QgsVectorLayer((processingFP + 'startLocationsCrit' + str(layerIndex + 1) + '.shp'), '', 'ogr')
    # Loop through the fields in this layer to find 'distance'
    for field in joinedLayer.fields():
        if field.name() == 'distance':
            with edit(joinedLayer):
                # Find the index number of the distance field.
                idx = joinedLayer.fields().indexFromName(field.name())
                # Use the index to identify and rename the field with a prefix relating to this iteration. 
                joinedLayer.renameAttribute(idx, (layerString[0:5].upper() + '_DIST'))

print('Done with Start Locations loop')

#########################
# if doing distance to boundaries, do it here#
############################

# Create a pointer to the final layer
startLocationsProcessed = iface.addVectorLayer((processingFP + 'startLocationsCrit' + str(len(layersList)) + '.shp'), 'startLocations', 'ogr')

# Use input data to calcuate thresholds, allocate indices, and calculate weights.
# Could potentially do this inside the processing loop, checking thresholds and weights, 
# but require dictionaries to be already built.

# Process suitability of competition areas: 
# Criteria 1: join table with usage 
paramDict = {
    'DISCARD_NONMATCHING' : False, 
    'INPUT' : 'C:/Users/helen/Documents/Assignment5/inputData/compAreas_OV.shp', 
    'FIELD' : 'Map_Name', 
    'INPUT_2' : 'C:/Users/helen/Documents/Assignment5/inputData/compAreaUse2019_OV.csv', 
    'FIELD_2' : 'MapName', 
    'FIELDS_TO_COPY' : ['UsedInSeason'], 
    'METHOD' : 1, 
    'OUTPUT' : 'C:/Users/helen/Documents/Assignment5/OPTDATA1/compAreas1.shp', 
    'PREFIX' : '' 
    }
processing.run('native:joinattributestable', paramDict)
#Create a pointer to the new layer for Criteria 1
compAreasCriteria1 = QgsVectorLayer()

# Criteria 2: check for freeways, roads or trainlines more than 200m from boundary
# Create a new buffered vector layer of the compeition areas where boundaries are reduced by 200m
paramDict = {
    'INPUT' : 'C:/Users/helen/Documents/Assignment5/inputData/compAreas_OV.shp', 
    'DISTANCE' : -200, 
    'SEGMENTS' : 5 
    'END_CAP_STYLE' : 0, 
    'JOIN_STYLE' : 0, 
    'MITER_LIMIT' : 2, 
    'DISSOLVE' : False, 
    'OUTPUT' : 'C:/Users/helen/Documents/Assignment5/outputData/compAreas200m.shp', 
    }
processing.run('native:buffer', paramDict)
# Create a pointer to the buffered layer
compAreasBuffered = QgsVectorLayer()

# Criteria 3: check for rivers
# Criteria 4: calculate area of parkland
# Criteria 5: intersect contours, sum their length, divide by area and 




for alg in QgsApplication.processingRegistry().algorithms():
    if "join" in alg.id():
        print(alg.id(), "-->", alg.displayName())


processing.algorithmHelp("native:buffer")




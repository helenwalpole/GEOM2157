###########################
#       ASSIGNMENT 5      #
#      MAJOR PROJECT      #
###########################

# import statements
import processing
#import math
from qgis.PyQt import QtGui
from PyQt5.QtCore import QVariant


# Create variables.
# These will be updated for the tool to reflect files and variables 
# selected by the user in the tool UI. 

# Set user-adjustable variables
stationsThreshold = 1000
toiletsThreshold = 200
drinkTapsThreshold = 200
playgroundsThreshold = 50
boundariesThreshold = 200
recentUseThreshold = 1
linearFeaturesThreshold = 200
riversThreshold = 1
parklandsThreshold = 15
hillsThreshold = 8 #fixed

# on a scale of 1-5, how important is: 
stationsWeight = 1
toiletsWeight = 5
drinkTapsWeight = 1
playgroundsWeight = 1
boundariesWeight = 3
recentUseWeight = 5
linearFeaturesWeight = 1
riversWeight = 2
parklandsWeight = 5
hillsWeight = 5
startsWeight = 3

# Set the fixed variables
freewaysThreshold = 200
riverThreshold = True

# Set filepaths
inputFP = 'C:/Users/helen/Documents/Assignment5/inputData/'
sourceFP = 'C:/Users/helen/Documents/Assignment5/sourceData/'
processingFP = 'C:/Users/helen/Documents/Assignment5/OPTDATA2/'

# Create two dictionaries from the user input to guide suitability criteria thresholds and weights.
thresholdsDict = {
    'stations' : stationsThreshold, 
    'toilets' : toiletsThreshold, 
    'drinkTaps' : drinkTapsThreshold, 
    'playgrounds' : playgroundsThreshold, 
    'recentUse' : recentUseThreshold, 
    'linearFeatures' : linearFeaturesThreshold, 
    'rivers' : riversThreshold, 
    'parklands' : parklandsThreshold, 
    'hills' : hillsThreshold}

weightsDict = {
    'stations' : stationsWeight, 
    'toilets' : toiletsWeight, 
    'drinkTaps' : drinkTapsWeight, 
    'playgrounds' : playgroundsWeight, 
    'recentUse' : recentUseWeight, 
    'linearFeatures' : linearFeaturesWeight, 
    'rivers' : riversWeight, 
    'parklands' : parklandsWeight, 
    'hills' : hillsWeight,
    'starts' : startsWeight}

# Create pointers to the input layers 
compAreasLayer = iface.addVectorLayer((inputFP + 'compAreas_OV.shp'), 'Layer', 'ogr')
startLocationsLayer = iface.addVectorLayer((inputFP + 'startLocations_OV.shp'), 'Layer', 'ogr')

# PREPARE DATA LAYERS



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
    'INPUT' : inputParam, #except for first iteration, this takes the output layer from the previous loop as input
    'DISCARD_NONMATCHING' : False, 
    'INPUT_2' : (sourceFP + layerString + '.shp'), #takes the correct join layer for this iteration
    'FIELDS_TO_COPY' : ['FID'], #all layers have this field 
    'MAX_DISTANCE' : None, 
    'NEIGHBORS' : 1, 
    'OUTPUT' : (processingFP + layerString + 'Join.shp'), 
    'PREFIX' : layerString[0:5].upper() + '_'
    }
    print(paramDict)
    # Run the joinbynearest algorithm using the dictionary
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

# Derive a new layer of competiton area boundaries from the compAreas polygon layer for later use. 
paramDict = {
    'INPUT' : (inputFP + 'compAreas_OV.shp'), 
    'OUTPUT': (sourceFP + 'boundaries.shp')
    }
processing.run('native:polygonstolines', paramDict)
#compOutlinesLayer = iface.addVectorLayer((sourceFP + 'boundaries.shp'), 'Layer', 'ogr')

# do a spatial join
# remove duplicates

# Create a pointer to the final layer
startLocationsProcessed = iface.addVectorLayer((processingFP + 'startLocationsCrit' + str(len(layersList)) + '.shp'), 'startLocationsProcessed', 'ogr')

# Use input data to calcuate thresholds, allocate indices, and calculate weights.
# Could potentially do this inside the processing loop, checking thresholds and weights, 
# but require dictionaries to be already built.

############################

# Process suitability of competition areas: 
# Criteria 1: join compAreas layer to the table of recently used compAreas in the previous season
paramDict = {
    'INPUT' : (inputFP + 'compAreas_OV.shp'), #replace with param 
    'DISCARD_NONMATCHING' : False, 
    'FIELD' : 'Map_Name', 
    'INPUT_2' : (inputFP + 'compAreaUse2019_OV.csv'), #replace with param 
    'FIELD_2' : 'MapName', 
    'FIELDS_TO_COPY' : ['UsedInSeason'], 
    'METHOD' : 1, 
    'OUTPUT' : (processingFP + 'compAreas1.shp'), 
    'PREFIX' : '' 
    }
processing.run('native:joinattributestable', paramDict)
#Create a pointer to the new layer for Criteria 1
compAreasCriteria1 = QgsVectorLayer((processingFP + 'compAreas1.shp'), '', 'ogr')

# Criteria 2: check for freeways, roads or trainlines more than 200m from boundary
# Create a new buffered vector layer of the competition areas where boundaries are reduced by 200m
paramDict = {
    'INPUT' : compAreasCriteria1, #replace with param 
    'DISTANCE' : -linearFeaturesThreshold, 
    'SEGMENTS' : 5, 
    'END_CAP_STYLE' : 0, 
    'JOIN_STYLE' : 0, 
    'MITER_LIMIT' : 2, 
    'DISSOLVE' : False, 
    'OUTPUT' : (processingFP + 'compAreas200m.shp'), 
    }
processing.run('native:buffer', paramDict)
# Create a pointer to the buffered layer
compAreasBuffered = QgsVectorLayer((processingFP + 'compAreas200m.shp'), '', 'ogr')

############# LOOP THROUGH RAIL, FREEWAYS AND ROADS?##########

#Check to see if train lines share any geometry with any features in this buffered layer. 
paramDict = { 
    'INPUT' : compAreasBuffered, 
    'DISCARD_NONMATCHING' : False, 
    'INPUT_2' : (sourceFP + 'trainlines.shp'), 
    'FIELDS_TO_COPY' : ['FID'], 
    'MAX_DISTANCE' : None, 
    'NEIGHBORS' : 1, 
    'OUTPUT' : (processingFP + 'trainlinesJoinDuplicates.shp'), 
    'PREFIX' : 'RAIL_' 
    }
# Run the joinbynearest algorithm using the dictionary
processing.run('native:joinbynearest', paramDict)

# The joinbynearest algorithm creates duplicate features if there is more than one 'nearest' feature inside the polygon. 
# Delete duplicate records. 
paramDict = { 
    'FIELDS' : ['Map_Name'], 
    'INPUT' : (processingFP + 'trainlinesJoinDuplicates.shp'), 
    'OUTPUT' : (processingFP + 'trainlinesJoin.shp') 
    }
processing.run('native:removeduplicatesbyattribute', paramDict)
    
# Remove extra fields added by the joinbynearest algorithm. 
#paramDict = { 
#    'COLUMN' : ['feature_x','feature_y','nearest_x','nearest_y', 'n', (layerString[0:5].upper() + '_' + 'FID')], 
#    'INPUT' : (processingFP + 'trainlinesJoin.shp'), 
#    'OUTPUT' : (processingFP + 'compAreas2.shp') 
#    }
#processing.run('native:deletecolumn', paramDict)

# Rename the newly-created distance field so we know it relates to trainlines.
joinedLayer = QgsVectorLayer((processingFP + 'trainlinesJoin.shp'), '', 'ogr')
# Loop through the fields in this layer to find 'distance'
for field in joinedLayer.fields():
    if field.name() == 'distance':
        with edit(joinedLayer):
            # Find the index number of the distance field.
            idx = joinedLayer.fields().indexFromName(field.name())
            # Use the index to identify and rename the field with a prefix relating to this iteration. 
            joinedLayer.renameAttribute(idx, 'RAIL_DIST')

# Join the RAIL_DIST field to the compAreas layer, as the above operations were performed on the buffered layer. 
# This is a 1:1 join, so we can use the joinattributestable algorithm. 
paramDict = {
    'INPUT' : compAreasCriteria1, #replace with param 
    'DISCARD_NONMATCHING' : False, 
    'FIELD' : 'FID', 
    'INPUT_2' : joinedLayer, 
    'FIELD_2' : 'FID', 
    'FIELDS_TO_COPY' : ['RAIL_DIST'], 
    'METHOD' : 1, 
    'OUTPUT' : (processingFP + 'compAreas2.shp'), 
    'PREFIX' : '' 
    }
processing.run('native:joinattributestable', paramDict)

# Create a pointer for this layer so we can use it again. 
compAreasCriteria2 = QgsVectorLayer((processingFP + 'compAreas2.shp'), '', 'ogr')

# Criteria 3: Check for rivers
# compAreasCriteria3 = QgsVectorLayer(XXXXXXXXXXXXX)
compAreasCriteria3 = compAreasCriteria2

# Criteria 4: Calculate proportion of competition area covered by parkland.
# Intersect the parkland with the compAreas so that we have accurate measurements of park area within each polygon. 
paramDict = { 
    'INPUT' : (sourceFP + 'parkland.shp'), 
    'INPUT_FIELDS' : [], 
    'OVERLAY' : compAreasCriteria3, 
    'OVERLAY_FIELDS' : ['FID'], 
    'OVERLAY_FIELDS_PREFIX' : '', 
    'OUTPUT' : (processingFP + 'parklandIntersect.shp'), 
    }
processing.run('native:intersection', paramDict)
# Create a pointer for this layer so we can use it again. 

# Use a spatial join to sum the area of parkland in each competition area
paramDict = {
    'INPUT' : compAreasCriteria3, 
    'JOIN' : (processingFP + 'parklandIntersect1.shp'), 
    'PREDICATE' : [0], 
    'JOIN_FIELDS' : ['Shape_Area'], 
    'SUMMARIES' : [5], 
    'DISCARD_NONMATCHING' : False, 
    'PREFIX': 'PARK_', 
    'OUTPUT' : (processingFP + 'parklandSums.shp'), 
    }
processing.run('qgis:joinbylocationsummary', paramDict)
# Create a pointer for this layer so we can use it again. 
joinedLayer = QgsVectorLayer((processingFP + 'parklandSums.shp'), '', 'ogr')

# Update each feature with the ratio of parkland to the total area of the compArea polygon. 
for i in joinedLayer.getFeatures():
    # Capture attribute values so we can replace NULLs with zeroes. 
    if i['UsedInSeas'] != NULL: 
        usedInSeason = int(i['UsedInSeas'])
    else: 
        usedInSeason = int(0)
    #print('usedInSeason is: ', usedInSeason)
        
    if i['Shape_Ar_1'] != NULL: 
        fltParkArea = float(i['Shape_Ar_1'])
    else: 
        fltParkArea = float(0)
    
    # Calculate the ratio of parkland 
    parkRatio = fltParkArea / i['Shape_Area']
    #print("Park ratio is: ", parkRatio)
    
    # overwrite the 'Shape_Ar_1' field with the new ratio value, and replace NULLs with 0s
    joinedLayer.startEditing()
    i['Shape_Ar_1'] = parkRatio
    i['UsedInSeas'] = usedInSeason
    joinedLayer.updateFeature(i)
    joinedLayer.commitChanges()
    ##NOTE: THIS PART OF THE SCRIPT IS VERY SLOW AND CAUSES A LONG LAG##

# Loop through the fields and update the name of 'Shape_Ar_1' to 'parkRatio'.
for field in joinedLayer.fields():
    if field.name() == 'Shape_Ar_1': 
        with edit(joinedLayer):
            # Get the index number of the 'Shape_Ar_1' field 
            idx = joinedLayer.fields().indexFromName(field.name())
            # Use the index to identify and rename the field
            joinedLayer.renameAttribute(idx, 'PARK_RATIO')

# Create a pointer for this layer so we can use it again. 
compAreasCriteria4 = joinedLayer 

########no syntax or runtime errors to here. Check for logic errors. #############
##### NO ERRORS TO HERE. NEED TO FIX NULLS IN SHAPE_AR_1 ###########

# Criteria 5: Intersect contours, sum their length, divide by area and 
# Intersect the parkland with the compAreas so that we have accurate measurements of park area within each polygon. 
paramDict = { 
    'INPUT' : (sourceFP + 'contours.shp'), 
    'INPUT_FIELDS' : [], 
    'OVERLAY' : compAreasCriteria4, 
    'OVERLAY_FIELDS' : ['FID'], 
    'OVERLAY_FIELDS_PREFIX' : '', 
    'OUTPUT' : (processingFP + 'contoursTrimmed.shp')
    }
processing.run('native:intersection', paramDict)
# Create a pointer for this layer so we can use it again. 
contoursTrimmed = QgsVectorLayer((processingFP + 'contoursTrimmed.shp'), '', 'ogr')

# Calculate the length of each trimmed contour polyline in contoursTrimmed
for i in contoursTrimmed.getFeatures(): 
    print(type(i))
    break 

# Use a spatial join to sum the length of contours in each competition area
paramDict = {
    'INPUT' : compAreasCriteria4, 
    'JOIN' : (processingFP + 'contoursTrimmed.shp'), 
    'PREDICATE' : [0], 
    'JOIN_FIELDS' : ['Shape_Le_1'], 
    'SUMMARIES' : [5], 
    'DISCARD_NONMATCHING' : False, 
    'PREFIX': 'HILLS_', 
    'OUTPUT' : 'C:/Users/helen/Documents/Assignment5/OPTDATA2/contourSums.shp', 
    }
processing.run('qgis:joinbylocationsummary', paramDict)

# Create a pointer for this layer so we can use it again. 
compAreasAllCriteria = QgsVectorLayer(XXXXXXXXXXXXX)



### SUITABILITY ANALYSIS CALCULATIONS
# Use mathematical operations to calculate final suitability scores 



for alg in QgsApplication.processingRegistry().algorithms():
    if "area" in alg.id():
        print(alg.id(), "-->", alg.displayName())

processing.algorithmHelp('native:intersection')




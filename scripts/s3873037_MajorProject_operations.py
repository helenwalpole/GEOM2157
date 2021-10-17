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
stationsThreshold = 500
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


############################
# PART 2: PROCESS THE SUITABIILTY OF START LOCATIONS
############################

# Calcuate distance of each start location from various features using 'joinbynearest'. 
# Loop this operation for each of the different types of features we are measuring. 

layersList = ['stations', 'toilets', 'drinkTaps', 'playgrounds']

for layerIndex, layerString in enumerate(layersList):
    # Set the input filepath for the first iteration to take the file from the 'inputFP' folder. 
    # After that, take files from the processing folder
    #print(layerIndex, layerString)
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
    #print(paramDict)
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
    print('Start critera done: ', layerString)
    print('Built startLocationsCrit' + str(layerIndex + 1) + '.shp')

print('StartLocations loop complete')

#########################
# if doing distance to boundaries, do it here#

# Derive a new layer of competiton area boundaries from the compAreas polygon layer for later use. 
paramDict = {
    'INPUT' : (inputFP + 'compAreas_OV.shp'), 
    'OUTPUT': (sourceFP + 'boundaries.shp')
    }
processing.run('native:polygonstolines', paramDict)
#compOutlinesLayer = iface.addVectorLayer((sourceFP + 'boundaries.shp'), 'Layer', 'ogr')
print('Built boundaries.shp')

###########################
# do a spatial join
# remove duplicates
###########################


# Create a pointer to the final layer
startLocationsAllCriteria = QgsVectorLayer((processingFP + 'startLocationsCrit' + str(len(layersList)) + '.shp'), 'startLocationsProcessed', 'ogr')

# Create a new field to save the final suitability score
dp = startLocationsAllCriteria.dataProvider()
dp.addAttributes([QgsField("SCORE",QVariant.Double, 'double', 5,2,)])
startLocationsAllCriteria.updateFields()
#print (startLocationsAllCriteria.fields().names())

# Calculate suitability scores using the dictionaries of thresholds and weights.
# For each criteria, retrieve the relevant distance value from the attribute table. 
# Allocate an index value based on the threshold from thresholdsDict. 
# Multiply the index value by the weight from weightsDict. 
# Store the final score in the attribute table. 

for i in startLocationsAllCriteria.getFeatures(): 
    stationsDist = i['STATI_DIST']
    toiletsDist = i['TOILE_DIST']
    drinkTapsDist = i['DRINK_DIST']
    playgroundsDist = i['PLAYG_DIST']
    
    # Calculate station score
    if stationsDist < thresholdsDict['stations']: 
        # Create an index in the range 0-1, where closer stations have a higher score than farther stations. 
        stationsIndex = 1 - stationsDist/thresholdsDict['stations']
    else: 
        stationsIndex = 0
    stationsScore = stationsIndex * weightsDict['stations']
    #print("stations", stationsDist, stationsIndex, stationsScore)
    
    # Calculate toilets score
    if toiletsDist < thresholdsDict['toilets']: 
        # Create an index in the range 0-1, where closer toilet facilities have a higher score than farther stations. 
        toiletsIndex = 1 - toiletsDist/thresholdsDict['toilets']
    else: 
        toiletsIndex = 0
    toiletsScore = toiletsIndex * weightsDict['toilets']
    #print("toilets", toiletsDist, toiletsIndex, toiletsScore)
    
    # Calcualte drink taps score
    if drinkTapsDist < thresholdsDict['drinkTaps']:
        # Create an index in the range 0-1, where closer drink taps have a higher score than farther stations. 
        drinkTapsIndex = 1 - drinkTapsDist/thresholdsDict['drinkTaps']
    else: 
        drinkTapsIndex = 0
    drinkTapsScore = drinkTapsIndex * weightsDict['drinkTaps']
    #print("drinkTaps", drinkTapsDist, drinkTapsIndex, drinkTapsScore)
    
    # Calcualte playgrounds score
    if playgroundsDist < thresholdsDict['playgrounds']:
        # Create an index in the range 0-1, where closer playgrounds have a higher score than farther stations. 
        playgroundsIndex = 1 - playgroundsDist/thresholdsDict['playgrounds']
    else: 
        playgroundsIndex = 0
    playgroundsScore = playgroundsIndex * weightsDict['playgrounds']
    #print("playgrounds", playgroundsDist, playgroundsIndex, playgroundsScore)
    
    finalScore = round((stationsScore + toiletsScore + drinkTapsScore + playgroundsScore),2)
    #print(finalScore)
    
    startLocationsAllCriteria.startEditing()
    i['SCORE'] = finalScore
    startLocationsAllCriteria.updateFeature(i)
    startLocationsAllCriteria.commitChanges()


############################
# PART 2: PROCESS THE SUITABIILTY OF COMPETITION AREAS
############################

# Criteria 1: Recently used competition areas. 
# Join compAreas layer to the table of recently used compAreas in the previous season. 
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
print('Built compAreas1.shp')

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
print('Built compAreas200m.shp')

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
print('Built trainlinesJoinDuplicates.shp')

# The joinbynearest algorithm creates duplicate features if there is more than one 'nearest' feature inside the polygon. 
# Delete duplicate records. 
paramDict = { 
    'FIELDS' : ['Map_Name'], 
    'INPUT' : (processingFP + 'trainlinesJoinDuplicates.shp'), 
    'OUTPUT' : (processingFP + 'trainlinesJoin.shp') 
    }
processing.run('native:removeduplicatesbyattribute', paramDict)
print('Built trainlinesJoin.shp')
    
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
print('Built compAreas2.shp')

# Create a pointer for this layer so we can use it again. 
compAreasCriteria2 = QgsVectorLayer((processingFP + 'compAreas2.shp'), '', 'ogr')
print('compAreas criteria 2 done')


# Criteria 3: Check for rivers
# compAreasCriteria3 = QgsVectorLayer(XXXXXXXXXXXXX)
compAreasCriteria3 = compAreasCriteria2

print('compAreas criteria 3 done')


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
    'JOIN' : (processingFP + 'parklandIntersect.shp'), 
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
print('Built parklandSums.shp')

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

print('Computed ratios to parklandSums.shp')

# Loop through the fields and update the name of 'Shape_Ar_1' to 'parkRatio'.
for field in joinedLayer.fields():
    if field.name() == 'Shape_Ar_1': 
        with edit(joinedLayer):
            # Get the index number of the 'Shape_Ar_1' field 
            idx = joinedLayer.fields().indexFromName(field.name())
            # Use the index to identify and rename the field
            joinedLayer.renameAttribute(idx, 'PARK_RATIO')

print('Renamed PARK_RATIO column')

# Create a pointer for this layer so we can use it again. 
compAreasCriteria4 = joinedLayer 
print('compAreas criteria 4 done')


# Criteria 5: Hilliness. 
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
print('Built contoursTrimmed.shp')

# Get and save the length of each trimmed contour polyline in contoursTrimmed.
# There are more than 2500 items in this layer, so this is going to be slow to process. 
# To avoid creating a new field, we can overwrite the values in an existing float field that we don't need. 
contoursTrimmed.startEditing()
for i in contoursTrimmed.getFeatures(): 
    i['ALTITUDE'] = float(i.geometry().length())
    contoursTrimmed.updateFeature(i)

contoursTrimmed.commitChanges()
print('Calculated contour length')

# Use a spatial join to sum the length of contours in each competition area.
paramDict = {
    'INPUT' : compAreasCriteria4, 
    'JOIN' : (processingFP + 'contoursTrimmed.shp'), 
    'PREDICATE' : [0], 
    'JOIN_FIELDS' : ['ALTITUDE'], 
    'SUMMARIES' : [5], 
    'DISCARD_NONMATCHING' : False, 
    #'PREFIX': 'HILLS_', 
    'OUTPUT' : (processingFP + 'contourSums.shp')
    }
processing.run('qgis:joinbylocationsummary', paramDict)

# Create a pointer for this layer so we can use it again. 
contourSums = QgsVectorLayer((processingFP + 'contourSums.shp'), '', 'ogr')
print('Build contourSums.shp')

# Rename the 'ALTITUDE_s' layer so we can use it to store the hillRatio values.
for field in contourSums.fields():
    if field.name() == 'ALTITUDE_s':
        with edit(contourSums):
            # Find the index number of the distance field.
            idx = contourSums.fields().indexFromName(field.name())
            # Use the index to identify and rename the field with a prefix relating to this iteration. 
            contourSums.renameAttribute(idx, 'HILL_RATIO')

# Calculate the ratio for each feature and save the result in the attribute table. 
for i in contourSums.getFeatures(): 
    # Replace nulls with zeroes
    if i['HILL_RATIO'] == NULL:
        contourSum = 0
    else: 
        contourSum = i['HILL_RATIO']
    
    #calculate length of contours(m) per square kilometre
    contourRatio = contourSum / i['Shape_Area'] * 1000000
    print('contour ratio: ', contourRatio)
    print('before: ', i['HILL_RATIO'])
    
    contourSums.startEditing()
    i['HILL_RATIO'] = contourRatio
    print('after: ', i['HILL_RATIO'])
    contourSums.updateFeature(i)
    contourSums.commitChanges()

print('Updated contour ratio column')

# Create a pointer for this layer so we can use it again. 
compAreasCrit5 = contourSums

# Criteria 6: Best start location. 
# Join higest scoring start location to the compAreas layer. 
paramDict = {
    'INPUT' : compAreasCrit5, 
    'JOIN' : startLocationsAllCriteria, 
    'PREDICATE' : [0], 
    'JOIN_FIELDS' : ['SCORE'], 
    'SUMMARIES' : [3], #Returns the maximum score for all start locations in this compArea
    'DISCARD_NONMATCHING' : False, 
    'PREFIX': 'SL_', 
    'OUTPUT' : (processingFP + 'compAreaBestSL.shp'), 
    }
processing.run('qgis:joinbylocationsummary', paramDict)

# Create a pointer for this layer so we can use it again. 
compAreasAllCriteria = QgsVectorLayer((processingFP + 'compAreaBestSL.shp'), 'Comp Areas All Criteria', 'ogr')

print('All Criteria complete')


### SUITABILITY ANALYSIS CALCULATIONS
# Use mathematical operations to calculate final suitability scores based on
# values the user selected in the interface. 

# Create a new field to save the final suitability score
dp = compAreasAllCriteria.dataProvider()
dp.addAttributes([QgsField("CA_SCORE",QVariant.Double, 'double', 5,2,)])
compAreasAllCriteria.updateFields()
#print (compAreasAllCriteria.fields().names())

# Create a variable to track the maximum suitability score, for use when classifying map symbology
scoreMax = 0.0

# Calculate suitabililty scores and save them in the new field.
for i in compAreasAllCriteria.getFeatures(): 
    # Assign attribute values to variables. 
    # Check for NULL values (which have the QVariant type) and replace with 0. 

    if type(i['UsedInSeas']) == QVariant: 
        recentUse = 0.0
    else: 
        recentUse = float(i['UsedInSeas'])
    
    if type (i['RAIL_DIST']) == QVariant: 
        linearFeaturesDist = 0.0
    else: 
        linearFeatureDist = float(i['RAIL_DIST'])
    
    if type(i['PARK_RATIO']) == QVariant:
        parksRatio = 0.0
    else:
        parksRatio = float(i['PARK_RATIO'])
    
    if type(i['HILL_RATIO']) == QVariant:
        hillsRatio = 0.0
    else: 
        hillsRatio = float(i['HILL_RATIO'])
    
    if type(i['SCORE_max']) == QVariant: 
        startLocsVal = 0.0
    else: 
        startLocsVal = float(i['SCORE_max'])
    
    # Calculate usage score.
    if recentUse <= thresholdsDict['recentUse']: 
        # Create an index in the range 0-1, where areas used less ofteh have a higher score.
        recentUseIndex = recentUse/thresholdsDict['recentUse']
        recentUseScore = round((recentUseIndex * weightsDict['recentUse']),2)
    else: 
        # Areas used more than the threshold score -1. 
        recentUseScore = -1
    #print('recentUse', recentUseDist, recentUseIndex, recentUseScore)
    
    # Calculate score for linear features (trainlines).
    if linearFeatureDist > 0:
        # Create a binary score. 
        # We are using nearest distance of a linear feature from a polygon representing the competition area reduced by the threshold distance. 
        # Therefore, if the distance is > 0, the linear feature has NOT entered the threshold distance into the competition area, so it scores 1. 
        # Where the distance is 0, the linear feature has extended into the competition area beyond the acceptable threshold , and scores 0. 
        linearFeatureIndex = 0
    else: 
        linearFeatureIndex = 1
    linearFeatureBinary = linearFeatureIndex * weightsDict['linearFeatures']
    
    #Calculate score for parkland.
    # Create a parabolic index in the range 0-1, centred on the ideal (threshold) distance 
    # Ratios below and above the threshold will score lower than the ideal. 
    if parksRatio <= (2 * thresholdsDict['parklands']): 
        parksIndex = 1 - (((parksRatio - thresholdsDict['parklands']) / thresholdsDict['parklands'])**2) 
    else: 
        parksIndex = 0
    parksScore = parksIndex * weightsDict['parklands']
    
    # Calculate score for hilliness.
    # Similar to parkland, we want a parabolic index in the range 0-1, centred on the preferred hilliness ratio.
    if hillsRatio <= (2 * thresholdsDict['hills']):
        hillsIndex = 1 - (((hillsRatio - thresholdsDict['hills']) / thresholdsDict['hills'])**2) 
    else: 
        hillsIndex = 0
    hillsScore = hillsIndex * weightsDict['hills']
    
    # Calculate score for start location.
    startLocsScore = startLocsVal * weightsDict['starts']
    
    
    # Calculate the final score. 
    # Sum the index criteria and multiply by the binary criteria to produce a raw (not standardised) score.
    rawScore = (recentUseScore + parksScore + hillsScore + startLocsScore) * linearFeatureBinary
    
    # Update the variable tracking the maximum finalScore
    if rawScore > scoreMax: 
        scoreMax = rawScore
        
    # Normalise the raw suitability scores using the maximum value.
    if rawScore > 0:
        finalScore = rawScore / scoreMax
    # Reclassify any scores of 0 as '-1'.
    else: 
        finalScore = -1
    
    print('Recent use:', recentUseScore, ', linear features:', linearFeatureIndex, ', parks:', parksIndex, ', hills:', hillsIndex, ', starts:', startLocsScore, '\nFINAL SCORE:', finalScore, ', Max score:', scoreMax)
    
    compAreasAllCriteria.startEditing()
    i['CA_SCORE'] = finalScore
    compAreasAllCriteria.updateFeature(i)
    compAreasAllCriteria.commitChanges()


# APPLY STYLES TO MAP LAYERS
#compAreaMap = QgisInterface.addVectorLayer(compAreasFinal, 'Competition Areas', 'ogr')
#startLocationMap = QgisInterface.addVectorLayer(startLocationsFinal, 'Start Locations', 'ogr')

tf = 'CA_SCORE'
rangeList = []
classesList = [-1, 0, 0.25, 0.5, 0.75, 1]
opacity = 1

# Symbology classes
for i,v in enumerate(classesList): #len(classesList): 
    # Avoid running the final loop, as we want to build one fewer class than items in the list. 
    if i == (len(classesList)-1):
        break 
    
    minval = classesList[i]
    maxval = classesList[(i+1)]
    classLabel = (str(maxval*100) + '% suitable')
    # Set the color range from pale purple for unsuitable to dark purple for most suitable. 
    # Use maxVal (which has a range of 0-1) to create the steps in the color. 
    color = QtGui.QColor((226-(156*maxval)), (200-(200*maxval)), (250-(110*maxval)))
    
    symbol = QgsSymbol.defaultSymbol(compAreasAllCriteria.geometryType())
    symbol.setColor(color)
    symbol.setOpacity(opacity)
    
    classRange = QgsRendererRange(minval, maxval, symbol, classLabel)
    print(classRange)
    rangeList.append(classRange)

print(rangeList)

# Apply ranges to layer
groupRenderer = QgsGraduatedSymbolRenderer('', rangeList)
groupRenderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
groupRenderer.setClassAttribute(tf)

compAreasAllCriteria.setRenderer(groupRenderer)

QgsProject.instance().addMapLayer(compAreasAllCriteria)

#
#for alg in QgsApplication.processingRegistry().algorithms():
#    if "area" in alg.id():
#        print(alg.id(), "-->", alg.displayName())
#
#processing.algorithmHelp('qgis:joinbylocationsummary')
#
#print(iface)



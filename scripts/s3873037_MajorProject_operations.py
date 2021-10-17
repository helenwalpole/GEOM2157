###########################
#       ASSIGNMENT 5      #
#      MAJOR PROJECT      #
###########################

# import statements
import processing
from qgis.PyQt import QtGui
from PyQt5.QtCore import QVariant


# Create variables.
# These will be updated for the tool to reflect files and variables 
# selected by the user in the tool UI. 

###############################
###   SET THESE VARIABLES   ###
###############################

# In the processing tool, these are determined by user input. 
# In this script, users can update these values manually. 

# How far is an acceptable distance for the following features from a start location? 
stationsThreshold = 500
toiletsThreshold = 200
drinkTapsThreshold = 200
playgroundsThreshold = 50
linearFeaturesThreshold = 200
parklandsThreshold = 15
recentUseThreshold = 1
hillsThreshold = 8 #fixed

# On a scale of 1-5, how important is: 
stationsWeight = 1
toiletsWeight = 5
drinkTapsWeight = 1
playgroundsWeight = 1
recentUseWeight = 5
linearFeaturesWeight = 1
parklandsWeight = 5
hillsWeight = 5
startsWeight = 3


################################
###   SET THESE FILE PATHS   ###
################################

# In the procesing tool, these filepaths are set by the user. 
# Here, they can be updated manually to reflect local files. 
# The three folders should correspond to the three folders downloaded from github. 

inputFP = 'C:/Users/helen/Documents/Assignment5/inputData/' #contains two .shp and two .csv files
sourceFP = 'C:/Users/helen/Documents/Assignment5/sourceData/' #contains nine .shp files 
processingFP = 'C:/Users/helen/Documents/Assignment5/processingData3/' #empty, ready to accept output data produced by this algorithm

################################
###   PROCESSING ALGORITHM   ###
################################

# Create two dictionaries from the user input to guide suitability criteria thresholds and weights.
thresholdsDict = {
    'stations' : stationsThreshold, 
    'toilets' : toiletsThreshold, 
    'drinkTaps' : drinkTapsThreshold, 
    'playgrounds' : playgroundsThreshold, 
    'recentUse' : recentUseThreshold, 
    'linearFeatures' : linearFeaturesThreshold, 
    'parklands' : parklandsThreshold, 
    'hills' : hillsThreshold}


weightsDict = {
    'stations' : stationsWeight, 
    'toilets' : toiletsWeight, 
    'drinkTaps' : drinkTapsWeight, 
    'playgrounds' : playgroundsWeight, 
    'recentUse' : recentUseWeight, 
    'linearFeatures' : linearFeaturesWeight, 
    'parklands' : parklandsWeight, 
    'hills' : hillsWeight,
    'starts' : startsWeight}

# Create pointers to the input layers 
compAreasLayer = QgsVectorLayer((inputFP + 'compAreas_OV.shp'), 'Layer', 'ogr')
startLocationsLayer = QgsVectorLayer((inputFP + 'startLocations_OV.shp'), 'Layer', 'ogr')


############################
#  ASSESS START LOCATIONS  #
############################

# Calcuate distance of each start location from various features using 'joinbynearest'. 
# Loop this operation for each of the different types of features we are measuring. 
layersList = ['stations', 'toilets', 'drinkTaps', 'playgrounds']

# Create a counter to track progress and provide feedback to the user. 
# The counter value is the total number of operations performed by this algorithm 
counter = 15.0

for layerIndex, layerString in enumerate(layersList):
    # Update the counter on each loop, progressing from 0-3
    percentComplete = (layerIndex/counter) * 100
    iface.statusBarIface().showMessage("Processed {}%".format(int(percentComplete)))
    
    # Set the input filepath for the first iteration to take the file from the 'inputFP' folder. 
    # After that, take files from the processing folder.
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

# Create a pointer to the final layer
startLocationsAllCriteria = QgsVectorLayer((processingFP + 'startLocationsCrit' + str(len(layersList)) + '.shp'), 'startLocationsProcessed', 'ogr')

# Create a new field to save the final suitability score
dp = startLocationsAllCriteria.dataProvider()
dp.addAttributes([QgsField("SCORE",QVariant.Double, 'double', 5,2,)])
startLocationsAllCriteria.updateFields()

# Update the counter to reflect progress
iface.statusBarIface().showMessage("Processed {}%".format(int(5/counter)))

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
    
    # Calculate toilets score
    if toiletsDist < thresholdsDict['toilets']: 
        # Create an index in the range 0-1, where closer toilet facilities have a higher score than farther stations. 
        toiletsIndex = 1 - toiletsDist/thresholdsDict['toilets']
    else: 
        toiletsIndex = 0
    toiletsScore = toiletsIndex * weightsDict['toilets']
    
    # Calcualte drink taps score
    if drinkTapsDist < thresholdsDict['drinkTaps']:
        # Create an index in the range 0-1, where closer drink taps have a higher score than farther stations. 
        drinkTapsIndex = 1 - drinkTapsDist/thresholdsDict['drinkTaps']
    else: 
        drinkTapsIndex = 0
    drinkTapsScore = drinkTapsIndex * weightsDict['drinkTaps']
    
    # Calcualte playgrounds score
    if playgroundsDist < thresholdsDict['playgrounds']:
        # Create an index in the range 0-1, where closer playgrounds have a higher score than farther stations. 
        playgroundsIndex = 1 - playgroundsDist/thresholdsDict['playgrounds']
    else: 
        playgroundsIndex = 0
    playgroundsScore = playgroundsIndex * weightsDict['playgrounds']
    
    finalScore = round((stationsScore + toiletsScore + drinkTapsScore + playgroundsScore),2)
    
    startLocationsAllCriteria.startEditing()
    i['SCORE'] = finalScore
    startLocationsAllCriteria.updateFeature(i)
    startLocationsAllCriteria.commitChanges()

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(6/counter)))

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

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(7/counter)))

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

#Check to see if linearFeatures (main roads, freeways, trainlines etc) share any geometry with any features in this buffered layer. 
paramDict = { 
    'INPUT' : compAreasBuffered, 
    'DISCARD_NONMATCHING' : False, 
    'INPUT_2' : (sourceFP + 'linearFeatures.shp'), 
    'FIELDS_TO_COPY' : ['FID'], 
    'MAX_DISTANCE' : None, 
    'NEIGHBORS' : 1, 
    'OUTPUT' : (processingFP + 'linearFeaturesJoinDuplicates.shp'), 
    'PREFIX' : 'LINE_' 
    }
# Run the joinbynearest algorithm using the dictionary
processing.run('native:joinbynearest', paramDict)
print('Built linearFeaturesJoinDuplicates.shp')

# The joinbynearest algorithm creates duplicate features if there is more than one 'nearest' feature inside the polygon. 
# Delete duplicate records. 
paramDict = { 
    'FIELDS' : ['Map_Name'], 
    'INPUT' : (processingFP + 'linearFeaturesJoinDuplicates.shp'), 
    'OUTPUT' : (processingFP + 'linearFeaturesJoin.shp') 
    }
processing.run('native:removeduplicatesbyattribute', paramDict)
print('Built linearFeaturesJoin.shp')
    
# Rename the newly-created distance field so we know it relates to trainlines.
joinedLayer = QgsVectorLayer((processingFP + 'linearFeaturesJoin.shp'), '', 'ogr')
# Loop through the fields in this layer to find 'distance'
for field in joinedLayer.fields():
    if field.name() == 'distance':
        with edit(joinedLayer):
            # Find the index number of the distance field.
            idx = joinedLayer.fields().indexFromName(field.name())
            # Use the index to identify and rename the field with a prefix relating to this iteration. 
            joinedLayer.renameAttribute(idx, 'LINE_DIST')

# Join the LINE_DIST field to the compAreas layer, as the above operations were performed on the buffered layer. 
# This is a 1:1 join, so we can use the joinattributestable algorithm. 
paramDict = {
    'INPUT' : compAreasCriteria1, #replace with param 
    'DISCARD_NONMATCHING' : False, 
    'FIELD' : 'FID', 
    'INPUT_2' : joinedLayer, 
    'FIELD_2' : 'FID', 
    'FIELDS_TO_COPY' : ['LINE_DIST'], 
    'METHOD' : 1, 
    'OUTPUT' : (processingFP + 'compAreas2.shp'), 
    'PREFIX' : '' 
    }
processing.run('native:joinattributestable', paramDict)
print('Built compAreas2.shp')

# Create a pointer for this layer so we can use it again. 
compAreasCriteria2 = QgsVectorLayer((processingFP + 'compAreas2.shp'), '', 'ogr')
print('compAreas criteria 2 done')

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(8/counter)))


# Criteria 3: Calculate proportion of competition area covered by parkland.
# Intersect the parkland with the compAreas so that we have accurate measurements of park area within each polygon. 
paramDict = { 
    'INPUT' : (sourceFP + 'parkland.shp'), 
    'INPUT_FIELDS' : [], 
    'OVERLAY' : compAreasCriteria2, 
    'OVERLAY_FIELDS' : ['FID'], 
    'OVERLAY_FIELDS_PREFIX' : '', 
    'OUTPUT' : (processingFP + 'parklandIntersect.shp'), 
    }
processing.run('native:intersection', paramDict)
# Create a pointer for this layer so we can use it again. 

# Use a spatial join to sum the area of parkland in each competition area
paramDict = {
    'INPUT' : compAreasCriteria2, 
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
        
    if i['Shape_Ar_1'] != NULL: 
        fltParkArea = float(i['Shape_Ar_1'])
    else: 
        fltParkArea = float(0)
    
    # Calculate the ratio of parkland 
    parkRatio = fltParkArea / i['Shape_Area']
    
    # overwrite the 'Shape_Ar_1' field with the new ratio value
    joinedLayer.startEditing()
    i['Shape_Ar_1'] = parkRatio
    i['UsedInSeas'] = usedInSeason
    joinedLayer.updateFeature(i)
    joinedLayer.commitChanges()

print('Computed ratios to parklandSums.shp')
# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(9/counter)))

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
compAreasCriteria3 = joinedLayer 
print('compAreas criteria 3 done')

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(10/counter)))


# Criteria 5: Hilliness. 
# Intersect the parkland with the compAreas so that we have accurate measurements of park area within each polygon. 

paramDict = { 
    'INPUT' : (sourceFP + 'contours.shp'), 
    'INPUT_FIELDS' : [], 
    'OVERLAY' : compAreasCriteria3, 
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

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(11/counter)))

# Use a spatial join to sum the length of contours in each competition area.
paramDict = {
    'INPUT' : compAreasCriteria3, 
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

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(12/counter)))

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
compAreasCrit4 = contourSums

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(13/counter)))


# Criteria 5: Best start location. 
# Join higest scoring start location to the compAreas layer. 
paramDict = {
    'INPUT' : compAreasCrit4, 
    'JOIN' : startLocationsAllCriteria, 
    'PREDICATE' : [0], 
    'JOIN_FIELDS' : ['SCORE'], 
    'SUMMARIES' : [3], #Returns the maximum score for all start locations in this compArea
    'DISCARD_NONMATCHING' : False, 
    'PREFIX': 'SL_', 
    'OUTPUT' : (processingFP + 'compAreaFinalRanking.shp'), 
    }
processing.run('qgis:joinbylocationsummary', paramDict)

# Create a pointer for this layer so we can use it again. 
compAreasAllCriteria = iface.addVectorLayer((processingFP + 'compAreaFinalRanking.shp'), 'Comp Areas All Criteria', 'ogr')

print('All Criteria complete')
# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(14/counter)))


### SUITABILITY ANALYSIS CALCULATIONS
# Use mathematical operations to calculate final suitability scores based on
# values the user selected in the interface. 

# Create a new field to save the final suitability score
dp = compAreasAllCriteria.dataProvider()
dp.addAttributes([QgsField("CA_SCORE",QVariant.Double, 'double', 5,2,)])
compAreasAllCriteria.updateFields()

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
    
    if type (i['LINE_DIST']) == QVariant: 
        linearFeaturesDist = 0.0
    else: 
        linearFeatureDist = float(i['LINE_DIST'])
    
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
    
    # Calculate score for linear features.
    # Create a binary score. 
    # We are using nearest distance of a linear feature from a polygon representing the competition area reduced by the threshold distance. 
    # Therefore, if the distance is > 0, the linear feature has NOT entered the threshold distance into the competition area, so it scores 1. 
    # Where the distance is 0, the linear feature has extended into the competition area beyond the acceptable threshold , and scores 0. 
    if weightsDict['linearFeatures'] == 'yes': # linear Features in the competition area are considered acceptable
        linearFeatureIndex = 1 # regardless of whether there are any linear features in the competition area 
    else: # if linear Features are considered unacceptable
        if linearFeatureDist == 0: #ie, there are linear features in the competition area
            linearFeatureIndex = 0
        else: # there are no linear features in the comp area to worry about
            linearFeatureIndex = 1
    linearFeatureScore = linearFeatureIndex
    
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
    rawScore = (recentUseScore + parksScore + hillsScore + startLocsScore) * linearFeatureScore
    
    # Update the variable tracking the maximum finalScore
    if rawScore > scoreMax: 
        scoreMax = rawScore
        
    # Normalise the raw suitability scores using the maximum value.
    if rawScore > 0:
        finalScore = rawScore / scoreMax
    # Reclassify any scores of 0 as '-1'.
    else: 
        finalScore = -1
    
    # Save the final score and update the feature. 
    compAreasAllCriteria.startEditing()
    i['CA_SCORE'] = finalScore
    compAreasAllCriteria.updateFeature(i)
    compAreasAllCriteria.commitChanges()

# Update progress bar 
iface.statusBarIface().showMessage("Processed {}%".format(int(counter/counter)))

##############################
# APPLY STYLES TO MAP LAYERS #
##############################

# Create a pointer to the field we want to use for the symbology.
tf = 'CA_SCORE'

# create variables we will use in the loop. 
rangeList = []
classesList = [-1, 0, 0.25, 0.5, 0.75, 1]
opacity = 1

# Create symbology classes
for i,v in enumerate(classesList): #len(classesList): 
    # Avoid running the final loop, as we want to build one fewer class than items in the list. 
    if i == (len(classesList)-1):
        break
    
    # Use the loop index to set the class range values 
    minval = classesList[i]
    maxval = classesList[(i+1)]
    
    # Create a label for the class based on the range 
    classLabel = (str(maxval*100) + '% suitable')
    
    # Set the color range from pale purple for unsuitable to dark purple for most suitable. 
    # Use maxVal (which has a range of 0-1) to create the steps in the color. 
    color = QtGui.QColor((226-(156*maxval)), (200-(200*maxval)), (250-(110*maxval)))
    
    # Allocate these values to the symbology 
    symbol = QgsSymbol.defaultSymbol(compAreasAllCriteria.geometryType())
    symbol.setColor(color)
    symbol.setOpacity(opacity)
    
    # Define the range for the renderer 
    classRange = QgsRendererRange(minval, maxval, symbol, classLabel)
    rangeList.append(classRange)

# Apply ranges to layer and update 
groupRenderer = QgsGraduatedSymbolRenderer('', rangeList)
groupRenderer.setClassificationMethod(QgsApplication.classificationMethodRegistry().method("EqualInterval"))
groupRenderer.setClassAttribute(tf)
compAreasAllCriteria.setRenderer(groupRenderer)

print('PROGRESS: Process complete')

# Remove progress from status bar 
iface.statusBarIface().clearMessage()
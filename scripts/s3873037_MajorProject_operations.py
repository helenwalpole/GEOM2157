###########################
#       ASSIGNMENT 5      #
#      MAJOR PROJECT      #
###########################

# import statements
import processing
#import math
from PyQt import QtGui


# Create variables.
# These will be updated for the tool to reflect files and variables 
# selected by the user in the tool UI. 

# Set user-adjustable variables
stationThreshold = 
toiletsThreshold = 
hillsRating = 
parklandThreshold = 

# Set filepaths
inputFP = 'C:/Users/helen/Documents/Assignment5/inputData/'
outputFP = 'C:/Users/helen/Documents/Assignment5/outputData/'
sourceFP = 'C:/Users/helen/Documents/Assignment5/sourceData/'

# add OV input layers to the map
compAreasLayer = iface.addVectorLayer((inputFP + 'compAreas_OV.shp'), 'Layer', 'ogc')
startLocationsLayer = iface.addVectorLayer((inputFP + 'startLocations_OV.shp'), 'Layer', 'ogc')



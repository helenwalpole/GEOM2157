# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber, 
                       QgsProcessingParameterRasterLayer, 
                       QgsProcessingParameterFeatureSource, 
                       QgsProcessingParameterFolderDestination, 
                       QgsVectorLayer,
                       QgsField,
                       QgsPointXY,
                       QgsProcessingParameterFeatureSink)
from qgis.gui import QgisInterface
from qgis import processing
import math


class OrienteeringVicSuitabilityAnalysis(QgsProcessingAlgorithm):
    """
    This algorithm assesses the suitability of a set of competition
    areas to host orienteering events.

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    
    ###TO UPDATE###
    CENTROIDSINPUT = 'buildingsFileName'
    LANDCOVERINPUT = 'landcoverFileName'
    OUTPUT = 'OUTPUT'
    DISTANCETHRESHOLD = 'distanceThreshold'
    VEGETATIONTHRESHOLD = 'vegetationThreshold'
    CENTRALAZIMUTH = 'centralAzimuth'
    AZIMUTHBAND = 'azimuthBand'
    FOLDERLOCATION = 'myfilePath'
    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return OrienteeringVicSuitabilityAnalysis()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'orienteeringvicsuitabilityanalysis'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Orienteering Vic Suitability Analysis')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        
        ###TO UPDATE###
        return self.tr("This algorithm takes a classified landcover raster and a set of building centroids (vector points) as inputs and returns a polygon layer with buildings classified according to their fire vulnerability.\n"
        + "Fire vulnerability is assessed in relation to three factors: a structure's proximity to other structures, a structure's proximity to vegetation, and the presence of other structures upwind of the structure."
        + "The algorithm takes the following as inputs: \n"
        + "A vector point layer indicating building centroids\n"
        + "A raster layer with landcover classification\n"
        + "The minimum safe distance for a neighbouring structure (in metres)\n"
        + "The minimum safe percentage of vegetation in the surrounding 30m area (in metres)\n"
        + "The current wind direction (as a compass direction)\n"
        + "The range of directions for which the wind is considered dangerous (eg, within 30 degrees)\n")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """      
        
        # We add the input vector features source for the building centroids. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CENTROIDSINPUT,
                self.tr('Input vector layer with building centroids'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        # We add the input raster source for the landcover classification.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.LANDCOVERINPUT,
                self.tr('Input raster layer with landcover classification'), 
            )
        )
        
        # We add the input value for the distance theshold. 
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCETHRESHOLD,
                self.tr('Threshold safe distance from other structures (in metres)'),
                defaultValue=20
            )
        )
        
        # We add the input value for the vegetation theshold. 
        self.addParameter(
            QgsProcessingParameterNumber(
                self.VEGETATIONTHRESHOLD,
                self.tr('Threshold percentage of area within 30m that is vegetation'),
                defaultValue=25
            )
        )
        
        # We add the input value for the wind direction (in compass degrees). 
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CENTRALAZIMUTH,
                self.tr('Current wind direction (in compass degrees)'),
                defaultValue=270
            )
        )
        
        # We add the input value for the range of wind directions. 
        self.addParameter(
            QgsProcessingParameterNumber(
                self.AZIMUTHBAND,
                self.tr('Threshold angle for wind direction (eg, "within 30 degrees"), (in compass degrees)'),
                defaultValue=30
            )
        )
        
        # We add the input value for the folder location to save the output file. 
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.FOLDERLOCATION,
                self.tr('Select a folder to save your output file')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # create variables from user input
        vectorBuildingsLayer = self.parameterAsVectorLayer(parameters, self.CENTROIDSINPUT, context)
        rasterLayer = self.parameterAsRasterLayer(parameters, self.LANDCOVERINPUT, context)
        distanceThreshold = self.parameterAsDouble(parameters, self.DISTANCETHRESHOLD, context)
        vegetationThreshold = self.parameterAsDouble(parameters, self.VEGETATIONTHRESHOLD, context)
        centralAzimuth = self.parameterAsDouble(parameters, self.CENTRALAZIMUTH, context)
        azimuthBand = self.parameterAsDouble(parameters, self.AZIMUTHBAND, context)
        myFilePath = self.parameterAsString(parameters, self.FOLDERLOCATION, context)
#        myFilePath = 'C:/Users/helen/Documents/Mod04AssessedEx3/'

        
        # Buffer each house to 30m (not dissolved)
        # Run the buffer algorithm and save the output to file
        processing.run('native:buffer', {
            'INPUT': vectorBuildingsLayer, 
            'DISTANCE': 30, 
            'SEGMENTS': 10, 
            'END_CAP_STYLE': 0, 
            'JOIN_STYLE': 0, 
            'DISSOLVE': False, 
            'OUTPUT': myFilePath + 'bldg_buffer11.shp'
            }
        )
        # Create a handle for the buffered polygons layer.
        bufferLayer = QgsVectorLayer((myFilePath + 'bldg_buffer11.shp'), 'BuildingsBuffered', 'ogr')

        # Use the zonal histogram tool to count number of pixels in each landcover class within buffer zone. 
        processing.run('native:zonalhistogram', {
            'INPUT_RASTER': rasterLayer,
            'RASTER_BAND': 1, 
            'INPUT_VECTOR': bufferLayer,
            'COLUMN_PREFIX': 'COUNT',
            'OUTPUT': myFilePath + 'histogram'
            }
        )
        # Create a handle for the histogram data.
        histoLayer = QgsVectorLayer((myFilePath + 'histogram.gpkg'), 'HistogramLayer', 'ogr')

        # Use the distance matrix tool to calculate the distance between each building and its nearest neighbour.
        processing.run('qgis:distancematrix', {
            'INPUT': vectorBuildingsLayer, 
            'INPUT_FIELD': 'OBJECTID', 
            'TARGET': vectorBuildingsLayer,
            'TARGET_FIELD': 'OBJECTID', 
            'MATRIX_TYPE': 0, 
            'NEAREST_POINTS': 1,
            'OUTPUT': myFilePath + 'nnDistanceMatrix'
            }
        )
        # Create a handle for the nearest neighbour points layer.
        matrixLayer = QgsVectorLayer((myFilePath + 'nnDistanceMatrix.gpkg'), 'NearestNeighbourMatrix', 'ogr')

        # Join the nearest neighbour distance data from the points layer to the buffered buildings polygon layer.
        processing.run('qgis:joinattributestable', {
            'INPUT': histoLayer, 
            'FIELD': 'OBJECTID', 
            'INPUT_2': matrixLayer, 
            'FIELD_2': 'InputID', 
            'FIELDS_TO_COPY': ['TargetID', 'Distance'],
            'METHOD': 1, 
            'DISCARD_NONMATCHING': True, 
            'PREFIX': '', 
            'OUTPUT': myFilePath + 'bufferedWithDistances11', 
            'NON_MATCHING': myFilePath + 'bufferedWithDistancesRejected'
            }
        )
        # Add this new polygon layer showing buffered polygons to the map.
        distancesBuffer = QgsVectorLayer((myFilePath + 'bufferedWithDistances11.gpkg'), 'BuildingsWithScores', 'ogr')

        # In the new layer, add new fields to hold the percentage vegetation and vulnerability classification values
        distancesBuffer.startEditing()
        distancesBuffer.addAttribute(QgsField('VEG_PERCENTAGE', QVariant.Double))
        distancesBuffer.addAttribute(QgsField('VULNERABIILTY', QVariant.String))
        distancesBuffer.addAttribute(QgsField('NN_AZIMUTH', QVariant.Double))
        distancesBuffer.updateFields()
        distancesBuffer.commitChanges()

        # Calculate area of each pixel in the raster (the ground length of 1 pixel is 60cm)
        pixelArea = 0.6 * 0.6

        # Calculate area of each building's buffered circle (as speficied by user and stored as distanceThreshold).
        totalArea = math.pi * distanceThreshold * distanceThreshold

        # Create an iterable list of features. 
        bufferZones = distancesBuffer.getFeatures()

        # Loop through all the buffered structures. 
        for bufferZone in bufferZones:
            # Calculate azimuth between the two nearest neighbours noted for each point in the attribute table of the buffered structures. 
            # Extract the featureID numbers for the relevant points from the feature 
            point1id = bufferZone['OBJECTID']
            point2id = bufferZone['TargetID']
            
            # Create an interable set of features from the original 'bldg_cetroids' feature layer
            bldgPoints = vectorBuildingsLayer.getFeatures()
            
            # Loop through the layer of building centroids to match the objectIDs to points. 
            # When a match is found, save the related point as a QgsPointXY object. 
            # Stop once two matches are found (to save on processing time)
            point1xy = QgsPointXY()
            point2xy = QgsPointXY()
            count = 0
            
            for bldgPoint in bldgPoints: 
                if bldgPoint['OBJECTID'] == point1id:
                    point1xy = bldgPoint.geometry().asPoint()
                    #print('new point1xy is: ', point1xy)
                    count += 1
                    continue
                elif bldgPoint['OBJECTID'] == point2id:
                    point2xy = bldgPoint.geometry().asPoint()
                    #print('new point2xy is: ', point2xy)
                    count += 1
                elif count ==2: 
                    break 
                
            # Calculate the azimuth between the two points. 
            # this algorithm returns a value between -180 and 180
            fltAzimuth = point1xy.azimuth(point2xy)
            #print(fltAzimuth)
            
            # Ensure centralAzimuth falls within the same range as fltAzimuth (-180 to 180)
            centralAzimuth = (((centralAzimuth + 180) %360) - 180)
            
            # Determine if the fltAzimuth is within a certain angle (azimuthBand) of the specified input bearing (centralAzimuth).   
            # Handle the edge case when the azimuth is closer to the end of the range than the azimuth band. 
            azimuthMinimum = centralAzimuth - azimuthBand
            azimuthMaximum = centralAzimuth + azimuthBand
            
            if azimuthMaximum > 180:
                if -180 <= fltAzimuth <= (azimuthMaximum - 360) or azimuthMinimum <= fltAzimuth <= 180:
                    azimuthRating = 'danger'
                else:
                    azimuthRating = 'safe'

            elif azimuthMinimum < -180: 
                if -180 <= fltAzimuth <= azimuthMaximum or (azimuthMinimum + 360) <= fltAzimuth <= 180:
                    azimuthRating = 'danger'
                else:
                    azimuthRating = 'safe'
            else: 
                if azimuthMinimum <= fltAzimuth <= azimuthMaximum:
                    azimuthRating = 'danger'
                else:
                    azimuthRating = 'safe'
            
            # Calculate the total area of vegetation (category 4 = grass, category 5 = trees)
            vArea = bufferZone['COUNT4'] + bufferZone['COUNT5']
            
            # Calculate percentage of this buffered area that's vegetation 
            vPercent = (vArea * pixelArea) / totalArea * 100
            #print(vPercent, '%')
            
            # Use logic to determine which vulnerability category this structure falls into. 
            if bufferZone['Distance'] < distanceThreshold: 
                if azimuthRating == 'danger': 
                    if vPercent > vegetationThreshold:
                        vClass = 'high vulnerability'
                    else: 
                        vClass = 'medium vulnerability'
                else: 
                    if vPercent > vegetationThreshold: 
                        vClass = 'medium vulnerability'
            else: 
                vClass = 'low vulnerability'
            
            # Update the attribute table with our calculated values for percent vegetation, vulnerability category and azimuth to nearest neighbour
            distancesBuffer.startEditing()
            bufferZone['VEG_PERCENTAGE'] = vPercent
            bufferZone['VULNERABIILTY'] = vClass
            bufferZone['NN_AZIMUTH'] = fltAzimuth
            distancesBuffer.updateFeature(bufferZone)
            distancesBuffer.commitChanges()

        return {}

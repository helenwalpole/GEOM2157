# GEOM2157
Geospatial Programming (RMIT University)

This script and associated data has been created by Helen Walpole (s3873037) for assessment. 

Two scripts are provided. One runs in the python script editor, the other runs from the QGIS processing toolbox. 
Both use the same files in the inputData and sourceData folders. 

Instructions for running 

1.	Go to https://github.com/helenwalpole/GEOM2157/tree/master 

2.	Download these three folders from github and save them in the same directory: 
a.	Scripts
b.	sourceData (should contain 9 shapefiles)
c.	inputData (should contain 2 shapefiles and 1 csv)

3.	Create a new folder for your processed data in the same directory, called 'processingData'. It is recommended that you create a new folder to store the processed data each time you run the algorithm (eg, processingData1/)


To run the python script (s3873027_MajorProject_operations.py)
-	Open in Qgis script editor 
-	Set file path (lines 44-46) to reflect the directories you created above. 

To run the python processing tool (s3873037_MajorProject_QgisTool.py): 
-	In the processing toolbox, click the python menu and click 'open existing script'
-	Browse to the script location
-	In the dialog, select the three directories you created above when prompted for input, source and output data. 

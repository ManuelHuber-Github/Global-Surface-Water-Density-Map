# Global-Surface-Water-Density-Map
This repository is a manual to produce globally scaled surface water density maps using Google Earth Engine and Python. The aim of this work is to create an easy-to-apply method-
ology to create global surface water density maps. Here, two characteristics need to be variable: 1) Resolution and 2) Input Reference data. Keeping these two variables adjustable allowsto produce density maps on a custom resolution and input data. The following figure shows a 25km resolution surface water density map using the MERIT hydrograph map (https://developers.google.com/earth-engine/datasets/catalog/MERIT_Hydro_v1_0_1#description). It descibes the percentage of water within a grid cell (25x25km).
![merit_zoom_all_V2](https://user-images.githubusercontent.com/62883629/158180961-14a3da8e-88ff-44bb-9be4-2a1a6c0a5269.png)


The script was written in Python >3.6 (anaconda environment) on
Distributor ID: Ubuntu
Description:    Ubuntu 20.04.3 LTS
Release:        20.04
Codename:       focal. The scripts further require a Google Earth Engine account to use the cloud computing platfrom (https://earthengine.google.com/). The required python libaries are listed in the requirements.txt. 

Two scripts are provided:

1) Surface_Water_Density_Map_Python.py
2) ESA_WorldCover_Density_Map_Python.py

Both scripts produce global density maps. The advantage of the ESA_WorldCover map is that it allows to change land cover type. More information about the ESA_WorldCover map can be found here: https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100#bands

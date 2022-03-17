# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 14:34:24 2022

@author: Manuel Huber
"""



import os.path
import multiprocessing
from multiprocessing import Process, Manager
import ee
import geemap
import numpy as np
Map = geemap.Map()
import matplotlib.pyplot as plt
from colour import Color
#from osgeo import gdal
import pandas as pd
import time 
import os, glob
import progressbar
from osgeo import gdal
#########################################################################

def get_geotiff_gee(dataset,world,name, path, scale_x, name_save, tile_size,number_cover_type):
    
    sel_name = 'wld_rgn'    #country_na'
    conti = world.filter(ee.Filter.eq(sel_name, name)) # Select the right continent boundaries of the input name
    sel_name = 'country_na' 
    features_country = np.unique(conti.aggregate_array(sel_name).getInfo()) # All countries in the selected continents/area

    bar = progressbar.ProgressBar(maxval=len(features_country), \
        widgets=[progressbar.Bar('=', '[', ']'), ' ', '{}'.format(name), progressbar.Percentage()])
    bar.start()
    # Looping through all countries individually as there are limitations on the "coveringGrid" function, which needs to put into a list:
    for j in range(len(features_country)):
        bar.update(j+1)
        geometry = world.filter(ee.Filter.eq(sel_name, features_country[j]))
        ROI = geometry.geometry() 
    

        data_pro = dataset.projection()
        features  = ROI.coveringGrid(data_pro,tile_size)  #Set the size of the tiling which will depend on the inital resolution set! 
        geometries_new  = features.toList(5000)
    

        for k in range(len(geometries_new.getInfo())):
    
            roi =ee.Feature(geometries_new.getInfo()[k]).geometry()
        
            ##########!!!!!!!!!!!!!!! Depending on dataset!!!!!!!!!!!!!!!!!!!!############
            # Here the right feaure or layer is selected from the input dataset
            data = dataset.updateMask(dataset.eq(number_cover_type)).clip(roi)
            ##########!!!!!!!!!!!!!!! Depending on dataset!!!!!!!!!!!!!!!!!!!!############
 
            
    
            data_pro = data.projection();   # Select projection of the image
    
             # Force the next reprojection to aggregate instead of resampling.
            new_area_count = data.reduceResolution(**{'reducer': ee.Reducer.count(),'bestEffort': True, 'maxPixels':65536}).reproject(data_pro,None, scale_x)
            new_area_count_all = data.unmask().reduceResolution(**{'reducer': ee.Reducer.count(),'bestEffort': True, 'maxPixels':65536}).reproject(data_pro, None ,scale_x)
            scaled_pixels =new_area_count.divide(new_area_count_all.divide(100)) # ((Sum of selected pixels)/Total_Count_Pixels)*100 To get percent
            rio_pixels = scaled_pixels.clip(roi)
            
            #Possibility to mask certain vaules etc.:
            #imgUnmasked = rio_pixels.gt(0) #.select('b1')
            #umasked_data = rio_pixels.updateMask(imgUnmasked)
    
    
            if os.path.exists('{}/Image_Exported_{}_{}_{}_{}.tif'.format(path,scale_x,name_save,j,k)) == False:
                geemap.ee_export_image(rio_pixels , filename='{}/Image_Exported_{}_{}_{}_{}.tif'.format(path,scale_x,name_save,j,k), scale= scale_x, region = ROI)
                #print(name_save,  features_country[j], k)
            #else:
               # print('This file already exists: ',name_save,k,features_country[j])
                
            if os.path.exists('{}/Image_Exported_{}_{}_{}_{}.tif'.format(path,scale_x,name_save,j,k)) == False:
                file_object =  open('{}Missing_Files.txt'.format(path), 'a')
                file_object.write('{}, {}, {}, '.format(name_save,  features_country[j], k))
                file_object.write("\n")
                # Close the file
                file_object.close()
                print(name_save,  features_country[j], k, 'Is still missing - Download process failed - Will be downloaded in smaller patches')
                
            # Backup download in case there is downloading issue with the set tilesize
            if os.path.exists('{}/Image_Exported_{}_{}_{}_{}.tif'.format(path,scale_x,name_save,j,k)) == False: 
                features_2  = roi.coveringGrid(data_pro, 200000)
                geometries_new_2  = features_2.toList(5000)#.map(func_yhi)
            
                
                for p in range(len(geometries_new_2.getInfo())):
        
                    roi_2 =ee.Feature(geometries_new_2.getInfo()[p]).geometry()
                    rio_pixels_2 = rio_pixels.clip(roi_2)
                    geemap.ee_export_image(rio_pixels_2 , filename='{}/Image_Exported_Failed_Down_{}_{}_{}_{}_{}.tif'.format(path,scale_x,name_save,j,k,p), scale= scale_x, region = roi_2)

                
    bar.finish()

#####################  Start the first the mining process in Google Earth Engine ##############################

"""
10	006400	Trees
20	ffbb22	Shrubland
30	ffff4c	Grassland
40	f096ff	Cropland
50	fa0000	Built-up
60	b4b4b4	Barren / sparse vegetation
70	f0f0f0	Snow and ice
80	0064c8	Open water
90	0096a0	Herbaceous wetland
95	00cf75	Mangroves
100	fae6a0	Moss and lichen

https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100#bands

"""

if __name__ == "__main__":
    
    ##### Input - user depndend ##########################
    name = 'ESA_WorldCover_Trees' # Select name at which data will be sotred with
    dataset = ee.ImageCollection("ESA/WorldCover/v100").first()     
    number_cover_type = 10
    
    path_save = '/data/River_Density/New_River_Composition_Different_Res/'
    
    folder_name = 'Test_Folder'
    if os.path.exists('{}{}'.format(path_save,folder_name)) == False:
        os.mkdir('{}{}'.format(path_save,folder_name))
    path ='{}{}/'.format(path_save,folder_name)
    scale_x= 25000  #In m ==> 25km 
    tile_size = 500000
    
    number_of_processors = 4
    ######################################################
    
    world = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017") # Feature collection which gives boundaries for countries and continents
    sel_name =  'wld_rgn' # if interested for countries select 'country_na'
    europe = world# Here is also option to select individual countries or continents, e.g. filter(ee.Filter.eq('wld_rgn', 'Europe'))

    features_cont = np.array(['North America','Africa' , 'Australia', 'Caribbean' ,'Central America',
                 'Central Asia' ,'E Asia', 'Europe' ,'Indian Ocean', 'N Asia' ,
                 'Oceania', 'S Asia', 'S Atlantic' ,'SE Asia', 'SW Asia', 'South America'])
    # To avoid spaces an addtional list of names has been created:
    features_cont_name = np.array(['North_America','Africa' , 'Australia', 'Caribbean' ,'Central_America',
                 'Central_Asia' ,'E_Asia', 'Europe' ,'Indian_Ocean', 'N_Asia' ,
                 'Oceania', 'S_Asia', 'S_Atlantic' ,'SE_Asia', 'SW_Asia', 'South_America'])
    
    # Creating a list to split the processes to the provided cores (this case 5 processes in parallel)
    x = np.arange(len(features_cont))
    split = np.array_split(x, number_of_processors) # Here the number of processors can be selected
    print(split, len(split))
    
    for s in range(len(split)):
    #for s in range(1):
        print('Split', s+1, 'out of ', len(split))
        
        area_sel = features_cont[split[s]]
        area_sel_name = features_cont_name[split[s]]
        manager = multiprocessing.Manager()
        print('entering the processing')
    
        df_all = manager.list()
        processes = []
        for j in range(len(area_sel)):
            
            name_save = area_sel_name[j]
            name_inp = area_sel[j]
            print(name_inp, 'is in the making')
            p = Process(target=get_geotiff_gee, args=(dataset,world,name_inp, path, scale_x, name_save,tile_size,number_cover_type,))  # Passing the list
            p.start()
            processes.append(p)
        
        for p in processes:
            p.join()


    print('Finished first part. Now its time to look for the date line issue.')

    ####################### Downloading the areas along the date line separately to aviod feature cross over at -180,180!


    geometry_miss_1 =   ee.Geometry.Polygon(
            [[[158.84159346653087, 73.96789885519699],
              [158.84159346653087, 52.15339248067615],
              [179.84745284153087, 52.15339248067615],
              [179.84745284153087, 73.96789885519699]]])
    
    
    geometry_miss_2 =   ee.Geometry.Polygon(
            [[[-165.56270340846913, 73.72336873420824],
              [-165.56270340846913, 44.519635837378665],
              [-139.01973465846913, 44.519635837378665],
              [-139.01973465846913, 73.72336873420824]]])
    
    
    
    geometry_miss_all = [geometry_miss_1, geometry_miss_2]

    data_pro = dataset.projection()


    for i in range(len(geometry_miss_all)):
        ROI = ee.Feature(geometry_miss_all[i]).geometry()

        features  = ROI.coveringGrid(data_pro, 1000000)

        geometries_new  = features.toList(5000)#.map(func_yhi)

        list_images = []
        for k in range(len(geometries_new.getInfo())):

            roi =ee.Feature(geometries_new.getInfo()[k]).geometry()


            ##########!!!!!!!!!!!!!!! Depending on dataset!!!!!!!!!!!!!!!!!!!!############
            data = dataset.updateMask(dataset.eq(number_cover_type)).clip(roi)
            ##########!!!!!!!!!!!!!!! Depending on dataset!!!!!!!!!!!!!!!!!!!!############


            data_pro = data.projection();   # Select projection of the image

             # Force the next reprojection to aggregate instead of resampling.
            new_area_count = data.reduceResolution(**{'reducer': ee.Reducer.count(),'bestEffort': True, 'maxPixels':65536}).reproject(data_pro,None, scale_x)
            new_area_count_all = data.unmask().reduceResolution(**{'reducer': ee.Reducer.count(),'bestEffort': True, 'maxPixels':65536}).reproject(data_pro, None ,scale_x)
            scaled_pixels =new_area_count.divide(new_area_count_all.divide(100)) # ((Sum of selected pixels)/Total_Count_Pixels)*100 To get percent
            rio_pixels = scaled_pixels.clip(roi)
            
            if os.path.exists('{}Image_Date_Line_Missing_{}_{}_{}_{}.tif'.format(path,scale_x,i,k,len(geometries_new.getInfo()))) == False: 
                geemap.ee_export_image(rio_pixels, filename='{}Image_Date_Line_Missing_{}_{}_{}_{}.tif'.format(path,scale_x,i,k,len(geometries_new.getInfo()) ), scale= scale_x, region = roi)

    print('All data is downloaded, its time to start creating some maps.')

    ######################### Merging and Reprojecting the data ###########################
    
    
    
    folder_name_2 =  'Reprojected_Files'
    if os.path.exists('{}{}'.format(path,folder_name_2)) == False:
        os.mkdir('{}{}'.format(path,folder_name_2))
    path_repro ='{}{}/'.format(path,folder_name_2)
    
    folder_name_3 =  'Final_Files'
    if os.path.exists('{}{}'.format(path,folder_name_3)) == False:
        os.mkdir('{}{}'.format(path,folder_name_3))
    path_final ='{}{}/'.format(path,folder_name_3)
    
    
    
    
    files_to_mosaic = glob.glob('{}/*.tif'.format(path))
    print(len(files_to_mosaic))
    
    files_string = " ".join(files_to_mosaic)
    
    for i in range(len(files_to_mosaic)):
        
        # Possibility to set projection
        command ='gdalwarp {} {}Out_{}.tif -overwrite -t_srs "+proj=longlat +ellps=WGS84"'.format(files_to_mosaic[i], path_repro,i)
        print(os.popen(command).read())
    
    
    
    files_to_mosaic = np.array(glob.glob('{}*.tif'.format(path_repro)))
    
    long = np.array_split(range(len(files_to_mosaic)), 5) # This needs to be done because gdal has a limit of geotiff files which can be processed at the same time
    
    for f in range(len(long)):
        
        files_ib = files_to_mosaic[long[f].astype(int)]
        print(len(files_to_mosaic))
        
        files_string = " ".join(files_ib)
        
        
        command = "gdal_merge.py -o {}inbetween_{}.tif -of gtiff -n 0 ".format(path_repro,f) + files_string
        print(os.popen(command).read())
    
    
    # Merging the inbetween files together
    files_to_mosaic = glob.glob('{}inbetween*.tif'.format(path_repro))
    
    files_string = " ".join(files_to_mosaic)
    
    
    command = "gdal_merge.py -o {}{}_{}.tif -of gtiff -n 0 ".format(path_final,scale_x,name) + files_string
    print(os.popen(command).read())
    
    command = "gdal_translate -scale -of KMLSUPEROVERLAY {}{}_{}.tif {}{}_{}.kmz".format(path_final,scale_x,name,path_final,scale_x,name)	
    print(os.popen(command).read())

"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


'''
This is the final subtiling script to create the input 2D arrays (satellite imagery, lidar data, and dem data) for the neural network. Written originally in Matlab by Chuck Abolt, then written and edited by Mia Mitchell in Santa Fe, New Mexico. Fall 2024. 
'''
import os
import numpy as np
import os
import geopandas as gpd
from shapely.geometry import box
import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
from shapely.geometry import box
from rasterio.coords import BoundingBox
from tqdm import tqdm
from rasterio.windows import Window
import argparse


def PrepareForestData(input_directory, output_directory, path_to_shapefile):
    """
    Description:
    ___________

    The main function for preparing satellite imagery, lidar data, and dem data into 2D arrays that are 512 x 512 pixels. 

    Parameters
    __________
    input_directory : str
        the input directory that holds the GeoTIFF files for subtiling
    output_directory : str
        the output directory to save the subtiled GeoTIFF files
    path_to_shapefile : str
        The path to the site shapefile provided in the .env file
    
   """

    shapefile_path = gpd.read_file(path_to_shapefile)
    wvfiles = []

    # Collect the .tif files in input directory
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.endswith('.tif'):
                wvfiles.append(os.path.join(root, file))

    # Progress Bar
    wvfile_pbar = tqdm(wvfiles, desc="Processing tiles", unit="tile", leave=True)
    for wvfile in wvfiles:
        filename = os.path.basename(wvfile)
        combined_name = f"{filename}"
        parts = combined_name.split('_')
        if len(parts) == 2:
            parts[1] = parts[1].split('.tif')[0]
            tract = f"{parts[0]}_{parts[1]}"
        else:
            parts[3] = parts[3].split('.tif')[0]
            tract = f"{parts[2]}_{parts[3]}"


        with rasterio.open(wvfile) as src:
            for i in range(2):
                for j in range(2):
                    subcode0 = f"{i}{j}"
                    window = Window(j * 976, i * 976, 1024, 1024)
                    try:
                        subwvimg = src.read(window=window)
                        assert subwvimg.shape[1:] == (1024, 1024)
                    except AssertionError:
                        #print(f"Skipping window {subcode0}: Shape mismatch {subwvimg.shape[1:]}")
                        continue

                    subwvimg = subwvimg.astype(float)
                    subwvimg[subwvimg == src.nodata] = np.nan
            

                    for ii in range(2):
                        for jj in range(2):
                            subcode1 = f"{ii}{jj}"
                            subwindow = Window(j * 976 + jj * 512, i * 976 + ii * 512, 512, 512)
                            try:
                                subsubwvimg = src.read(window=subwindow)
                                assert subsubwvimg.shape[1:] == (512, 512)
                            except AssertionError:
                                #print(f"Skipping subsubwindow {subcode0}-{subcode1}: Shape mismatch {subsubwvimg.shape[1:]}")
                                continue

                            subsubwvimg = subsubwvimg.astype(float)
                            subsubwvimg[subsubwvimg == src.nodata] = np.nan

                            if np.isnan(subsubwvimg).any() or np.all(subsubwvimg == 0):
                                #print(f"Skipping subwindow: {'Contains NaN values' if np.isnan(subsubwvimg).any() else 'All values are zero'}")
                                continue
                        

                            # Prepare filename and directories
                            if len(parts) == 2:
                                parts[1] = parts[1].split('.tif')[0]
                                tract = f"{parts[0]}_{parts[1]}"
                                fname = f"{tract}_{subcode0}_{subcode1}.tif"
                            else:
                                parts[3] = parts[3].split('.tif')[0]
                                tract = f"{parts[2]}_{parts[3]}"
                                fname = f"{parts[0]}_{parts[1]}_{tract}_{subcode0}_{subcode1}.tif"
                            output_path = os.path.join(output_directory, fname)

                            # Define transformation and save raster
                            transform = src.window_transform(subwindow)
                            with rasterio.open(
                                output_path, 'w',
                                driver='GTiff',
                                height=subsubwvimg.shape[1],
                                width=subsubwvimg.shape[2],
                                count=src.count,
                                dtype='int32', 
                                crs=src.crs,
                                transform=transform
                            ) as dst:
                                dst.write(subsubwvimg)
            wvfile_pbar.update(1) 
                            
 
    def tif_overlaps_shapefile(tif_path, shapefile_path):
        """
        Description
        ___________

        This function checks if the 512 x 512 tile intersects with the original shapefile.

        Parameters
        __________
        tif_path : str
            the path to the tif file path
        shapefile_path : geodataframe
            the shapefile for your site of interest
        
        Returns
        _______
        bool
            Whether the .tif intersects with the shapefile
        """
        gdf = gpd.read_file(shapefile_path)
        from shapely.geometry import box
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
        
        raster_bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
        raster_gdf = gpd.GeoDataFrame({'geometry': [raster_bbox]}, crs=gdf.crs)
        

        intersection = gdf.intersects(raster_gdf.geometry.iloc[0])
        if intersection.any():  
            pass
        else:
            #print("The shapefile does not intersect with the .tif file.")
            os.remove(tif_path)


    # Iterate over tif files 
    print("Evaluating whether all .tif files overlap with shapefile...")
    tif_files_pbar = tqdm(len(output_directory), desc="Processing tiles", unit="tile", leave=True)
    for tif_file in os.listdir(output_directory):
        tif_files_pbar.update(1) 
        if tif_file.endswith(".tif"):
            tif_path = os.path.join(output_directory, tif_file)
            #print(tif_path)
            if os.path.exists(tif_path):
                tif_overlaps_shapefile(tif_path, path_to_shapefile)
               
                    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tile GeoTIFFs into 512 x 512 arrays.')

    parser.add_argument('--input_directory', type=str, help='Path to the input directory of GeoTIFFs')
    parser.add_argument('--output_directory', type=str, help='Path to the output directory of tiled GeoTIFFs')
    parser.add_argument('--path_to_shapefile', type=str, help='Path to the site shapefile')
    args = parser.parse_args()


    PrepareForestData(args.input_directory, args.output_directory, args.path_to_shapefile)

 
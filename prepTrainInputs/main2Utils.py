"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""

import os
import math
import sys
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.windows import from_bounds, Window
import subprocess
import shutil
import zipfile
import osgeo.ogr as ogr
import osgeo.gdal as gdal
import numpy as np
from PIL import Image
from shapely.geometry import box, shape
import multiprocessing
from functools import partial
import xml.etree.ElementTree as ET
import geopandas as gpd
import pandas as pd
import json
from datetime import datetime
from itertools import combinations
import random
from typing import List, Union, Dict, Callable, Iterable, Optional, Any
from pyproj import CRS, Transformer
import re
from pathlib import Path
from glob import glob
from typing import List
import fiona
from shapely.ops import transform as shp_transform
import pdal
from urllib.parse import urlparse
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

def mergeTifs(inputPath, savePath, target_resolution=0.5):
    # If inputPath contains only a single zip file, unzip it and use the extracted contents
    if os.path.isdir(inputPath):
        items = [os.path.join(inputPath, item) for item in os.listdir(inputPath)]
        files = [item for item in items if os.path.isfile(item)]
        dirs = [item for item in items if os.path.isdir(item)]
        zip_files = [item for item in files if item.lower().endswith(".zip")]

        if len(zip_files) == 1 and len(files) == 1 and len(dirs) == 0:
            zip_path = zip_files[0]
            extract_dir = os.path.join(inputPath, "unzipped_contents")

            # Optional: clear old extracted contents before re-extracting
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir, exist_ok=True)

            print(f"Only zip found in inputPath. Extracting: {zip_path}")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            inputPath = extract_dir
            print(f"Using extracted contents from: {inputPath}")

    # Identify each subfolder within this folder
    subfolders = [f.path for f in os.scandir(inputPath) if f.is_dir()]

    os.makedirs(savePath, exist_ok=True)

    for subfolder in subfolders:
        tif_files = []
        metadata_xml = ""

        # Recursively search for all tif tiles and metadata xml in the subfolder
        for root, _, files in os.walk(subfolder):
            for file in files:
                if file.lower().endswith(".tif") and "P" in root:
                    tif_files.append(os.path.join(root, file))

                if file.lower().endswith(".xml") and "P" in root and "tif" not in file.lower():
                    metadata_xml = os.path.join(root, file)

        if not tif_files:
            print(f"No TIF files found in the subfolder: {subfolder}")
            continue

        # Parse metadata for tile ID
        tileID = ""
        if metadata_xml:
            print(f"metadata_xml: {metadata_xml}")
            tree = ET.parse(metadata_xml)
            root = tree.getroot()
            catid_elem = root.find(".//IMD/IMAGE/CATID")
            if catid_elem is not None:
                tileID = catid_elem.text
                print(f"tileID: {tileID}")
            else:
                print("catid_elem is none!")
        else:
            print("METADATA FILE NOT FOUND")

        # Output filename
        new_savePath = os.path.join(savePath, f"{tileID}.tif")

        # Merge the TIFs
        mosaic, out_trans = merge(tif_files)

        with rasterio.open(tif_files[0]) as src:
            src_crs = src.crs
            src_dtype = src.dtypes[0]
            count = src.count

        # Calculate aligned bounds
        left, top = out_trans.c, out_trans.f
        right = left + mosaic.shape[2] * out_trans.a
        bottom = top + mosaic.shape[1] * out_trans.e

        # Align bounds to target grid
        aligned_left = np.floor(left / target_resolution) * target_resolution
        aligned_bottom = np.floor(bottom / target_resolution) * target_resolution
        aligned_right = np.ceil(right / target_resolution) * target_resolution
        aligned_top = np.ceil(top / target_resolution) * target_resolution

        # New dimensions
        dst_width = int((aligned_right - aligned_left) / target_resolution)
        dst_height = int((aligned_top - aligned_bottom) / target_resolution)

        # New transform
        dst_transform = rasterio.transform.from_origin(
            aligned_left,
            aligned_top,
            target_resolution,
            target_resolution
        )

        # Metadata for the resampled output
        dst_meta = {
            "driver": "GTiff",
            "height": dst_height,
            "width": dst_width,
            "count": count,
            "dtype": src_dtype,
            "crs": src_crs,
            "transform": dst_transform
        }

        # Prepare destination array
        dst_array = np.zeros((count, dst_height, dst_width), dtype=src_dtype)

        # Resample
        for i in range(count):
            reproject(
                source=mosaic[i],
                destination=dst_array[i],
                src_transform=out_trans,
                src_crs=src_crs,
                dst_transform=dst_transform,
                dst_crs=src_crs,
                resampling=Resampling.bilinear
            )

        # Save the aligned and resampled raster
        with rasterio.open(new_savePath, "w", **dst_meta) as dst:
            dst.write(dst_array)

        print(f"Merged and resampled TIF saved to: {new_savePath}")


def checkCRS(directory, epsg):
    """
    Checks the Coordinate Reference System (CRS) of all TIF files in a given directory.
    
    Parameters:
    directory (str): The path to the directory containing the TIF files.
    epsg (str): The expected EPSG code for the CRS.
    """
    for filename in os.listdir(directory):
        if filename.endswith(".tif") or filename.endswith(".TIF"):
            tifPath = os.path.join(directory, filename)
            with rasterio.open(tifPath) as src:
                crs = src.crs
                assert crs.is_epsg_code, "The CRS is not in EPSG format."

                actualEPSG = crs.to_epsg()
                assert str(actualEPSG) == str(epsg), f"Expected EPSG code: {epsg}, Actual EPSG code: {actualEPSG}"
                print(f"EPSG code for {filename} is correct: {actualEPSG}")

def cropTif(inputTif, shp, outputTif, epsg):
    # Load the lidar shapefile
    lidar_shape = gpd.read_file(shp)

    # Check the CRS
    target_crs = CRS.from_epsg(int(epsg))
    if lidar_shape.crs != target_crs:
        print(f"Reprojecting from {lidar_shape.crs} to EPSG:{epsg}")
        lidar_shape = lidar_shape.to_crs(target_crs)
    else:
        print(f"Shapefile is already in EPSG:{epsg}")

    # Get the bounding box of the reprojected shapefile
    minx, miny, maxx, maxy = lidar_shape.total_bounds

    print(f'inputTif: {inputTif}')

    # First, crop the raster to the bounding box
    cropCmd = [
        "gdal_translate", "-projwin",
        str(minx), str(maxy), str(maxx), str(miny),
        inputTif, outputTif
    ]
    subprocess.run(cropCmd, check=True)

    # # Then, perform the mask on the cropped raster
    # warpCmd = [
    #     "gdalwarp", "-overwrite", "-of", "GTiff",
    #     "-tr", "0.5", "-0.5", "-tap",
    #     "-cutline", shp,
    #     inputTif, outputTif
    # ]
    # subprocess.run(warpCmd, check=True)

    # Remove the temporary cropped file
    # os.remove("temp_cropped.tif")

def saveWvimgMetadata(wvimgPath, savePath, wvimgMergedPath):
    metadata_dict = {}

    # Walk through the directory
    for root, dirs, files in os.walk(wvimgPath):
        for file in files:
            if file.endswith('XML') and 'PAN' in os.path.abspath(os.path.join(root, file)):
                full_path = os.path.join(root, file)
                x_vals = []
                y_vals = []
                
                # Parse the XML file
                tree = ET.parse(full_path)
                root = tree.getroot()

                # Extract the required information
                first_line_time = root.find('.//FIRSTLINETIME').text
                date = datetime.strptime(first_line_time[:10], '%Y-%m-%d').strftime('%Y-%m-%d')

                off_nadir = float(root.find('.//MEANOFFNADIRVIEWANGLE').text)
                target_azimuth = float(root.find('.//MEANSATAZ').text)
                solar_azimuth = float(root.find('.//MEANSUNAZ').text)
                solar_elevation = float(root.find('.//MEANSUNEL').text)
                tileID = root.find('.//IMD/IMAGE/CATID').text
                print(f'tileID: {tileID}')

                # extract the bounds of the tile (UTM)
                x_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/ULX').text))
                x_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/URX').text))
                x_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/LLX').text))
                x_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/LRX').text))

                y_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/ULY').text))
                y_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/URY').text))
                y_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/LLY').text))
                y_vals.append(float(root.find('.//IMD/MAP_PROJECTED_PRODUCT/LRY').text))

                min_x = min(x_vals)
                min_y = min(y_vals)
                max_x = max(x_vals)
                max_y = max(y_vals)

                # Store the information in the dictionary
                metadata_dict[tileID] = {
                    'filePath': os.path.join(wvimgMergedPath, f'{tileID}_merged.tif'),
                    'date': date,
                    'offNadir': off_nadir,
                    'targetAzimuth': target_azimuth,
                    'solarAzimuth': solar_azimuth,
                    'solarElevation': solar_elevation,
                    'min_x': min_x,
                    'min_y': min_y,
                    'max_x': max_x,
                    'max_y': max_y
                }

    # Save the metadata dictionary to a JSON file
    with open(savePath, 'w') as f:
        json.dump(metadata_dict, f, indent=4)


def generate_sensor_solar_tiles(metadata_json_path, output_directory):
    """
    Generate sensor and solar tiles for all elements in the metadata JSON file.
    
    :param metadata_json_path: Path to the JSON file containing metadata
    :param output_directory: Directory to save the output files
    """
    # Create 'sensor' and 'solar' subdirectories within the output directory
    sensor_dir = os.path.join(output_directory, 'sensor')
    solar_dir = os.path.join(output_directory, 'solar')
    os.makedirs(sensor_dir, exist_ok=True)
    os.makedirs(solar_dir, exist_ok=True)

    # Load metadata from file
    with open(metadata_json_path, 'r') as file:
        metadata = json.load(file)

    solar_max_global = float('-inf')
    sensor_max_global = float('-inf')

    # First pass to find global max values
    for file_path, data in metadata.items():
        _, solarNormal = getSolarNormal(data)
        _, sensorNormal = getSensorNormal(data)
        
        solar_max_global = max(solar_max_global, np.max(np.abs(solarNormal)))
        sensor_max_global = max(sensor_max_global, np.max(np.abs(sensorNormal)))

    solar_scale = solar_max_global / 128
    sensor_scale = 128 / sensor_max_global

    # Second pass to generate and save tiles
    for tileID, data in metadata.items():
        # get the tileID (key of the metadata)
        _, solarNormal = getSolarNormal(data)
        _, sensorNormal = getSensorNormal(data)

        solarNormal = (solarNormal / solar_scale + 128).astype(np.uint8)
        sensorNormal = (sensorNormal * sensor_scale + 128).astype(np.uint8)

        # Extract site name and date from file path
        site = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(data['filePath']))))
        date = datetime.strptime(data['date'], '%Y-%m-%d').strftime('%Y-%m-%d')

        # Save images in their respective subdirectories
        Image.fromarray(solarNormal).save(os.path.join(solar_dir, f"{tileID}.tif"))
        Image.fromarray(sensorNormal).save(os.path.join(sensor_dir, f"{tileID}.tif"))


def getSolarNormal(data):
    theta = data['solarElevation']
    phi = data['solarAzimuth']
    z0 = 10
    x0 = np.sqrt(z0**2 / (((np.tan(np.radians(theta)))**2) + (((np.tan(np.radians(theta)))**2) / (np.tan(np.radians(phi)))**2)))
    if phi > 180:
        x0 = x0 * -1
    y0 = x0 / np.tan(np.radians(phi))
    s = np.sqrt(x0**2 + y0**2 + z0**2)
    xn = x0 / s
    yn = y0 / s
    zn = z0 / s
    xg, yg = np.meshgrid(np.arange(-127.75, 128.25, 0.5), np.arange(-127.75, 128.25, 0.5))
    yg = np.flipud(yg)
    zg = -xn/zn * xg + -yn/zn * yg
    normal = zg
    return data, normal

def getSensorNormal(data):
    theta = 90 - data['offNadir']
    phi = (data['targetAzimuth']+180)%360
    z0 = 10
    x0 = np.sqrt(z0**2 / (((np.tan(np.radians(theta)))**2) + (((np.tan(np.radians(theta)))**2) / (np.tan(np.radians(phi)))**2)))
    if phi > 180:
        x0 = x0 * -1
    y0 = x0 / np.tan(np.radians(phi))
    s = np.sqrt(x0**2 + y0**2 + z0**2)
    xn = x0 / s
    yn = y0 / s
    zn = z0 / s
    xg, yg = np.meshgrid(np.arange(-127.75, 128.25, 0.5), np.arange(-127.75, 128.25, 0.5))
    yg = np.flipud(yg)
    zg = -xn/zn * xg + -yn/zn * yg
    normal = zg
    return data, normal

# --- helpers ---
def snap(x, res):
    # snap coordinate to nearest multiple of res
    return math.ceil(round(x / res) * res)

def process_tile(tile_info, pathToRaster, outputPath, crs, tileSize, res, datatype):
    i, j, left, top, stride_x, stride_y = tile_info

    # Compute tile origin using stride (NOT tileSize)
    tile_left = left + i * stride_x
    tile_top  =  top - j * stride_y
    tile_right  = tile_left + tileSize
    tile_bottom = tile_top  - tileSize

    # Snap to the pixel grid to avoid fractional pixels
    tile_left   = snap(tile_left,   res)
    tile_right  = snap(tile_right,  res)
    tile_top    = snap(tile_top,    res)
    tile_bottom = snap(tile_bottom, res)

    bbox = f"{tile_left} {tile_bottom} {tile_right} {tile_top}"

    # Name tiles by their upper-left corner
    if datatype == 'wvimg':
        outfile = os.path.join(
            outputPath,
            f"{os.path.splitext(os.path.basename(pathToRaster))[0]}_{int(tile_left)}_{int(tile_top)}.tif"
        )
    else:
        outfile = os.path.join(outputPath, f"{int(tile_left)}_{int(tile_top)}.tif")

    # keep output size fixed via bounds + res (produces 512x512 given 256m and 0.5m/px)
    projcmd = (
        f"rio warp {pathToRaster} {outfile} "
        f"--dst-crs {crs.to_string()} "
        f"--bounds {bbox} "
        f"--res {res} "
        f"--resampling cubic "
        f"--overwrite"
    )

    devnull = open(os.devnull, 'w')
    subprocess.call(projcmd, shell=True, stdout=devnull, stderr=devnull)

    # Optional quality checks
    with rasterio.open(outfile) as tile:
        data = tile.read()
        nodata_value = tile.nodata
        if datatype == 'wvimg':
            nodata_value = 0

        if nodata_value is not None:
            contains_nodata = (data == nodata_value).any()
            if contains_nodata:
                print(f"Tile {os.path.basename(outfile)} contains NoData ({nodata_value}).")
                os.remove(outfile)
                if datatype.lower() == 'chm':
                    print(f'REJECTING A CHM TILE WITH NO DATA')
                return False

    return True

def tileRaster(
    pathToRaster: str,
    outputPath: str,
    dataType: str,
    tileSize: int = 256,
    anchors_csv: str | Path = None,
    res: float = 0.5,
):
    """
    pathToRaster: input raster
    outputPath: output folder
    dataType: 'wvimg' or 'chm'
    tileSize: width/height in meters
    anchors_csv: path to CSV with columns ["X","Y"] for NW-corner anchors (in raster CRS)
    res: target pixel size (m/px)
    """
    if anchors_csv is None:
        raise ValueError("anchors_csv is required and must point to a CSV with columns ['X','Y'].")

    anchors_csv = Path(anchors_csv)
    if not anchors_csv.exists():
        raise FileNotFoundError(f"Anchors CSV not found: {anchors_csv}")

    # Load and validate anchors
    anchors = pd.read_csv(anchors_csv)
    if not {"X", "Y"}.issubset(anchors.columns):
        raise ValueError(f"Anchors CSV must contain columns ['X','Y']; got {list(anchors.columns)}")

    # Clean up anchors a bit
    anchors = anchors[["X", "Y"]].dropna().drop_duplicates()
    anchors["X"] = anchors["X"].astype(float)
    anchors["Y"] = anchors["Y"].astype(float)

    os.makedirs(outputPath, exist_ok=True)

    # Detect number of CPU cores
    num_cores = multiprocessing.cpu_count()
    num_workers = max(1, num_cores - 2)

    with rasterio.open(pathToRaster) as src:
        src_left, src_bottom, src_right, src_top = src.bounds
        crs = src.crs

        if crs is None or getattr(crs, "is_geographic", False):
            raise ValueError("Raster must be in a projected CRS (meters).")

        # Define tiles directly from anchors
        tile_info_list = []
        for x, y in anchors[["X", "Y"]].itertuples(index=False, name=None):
            x_left   = snap(x, res)
            y_top    = snap(y, res)
            x_right  = x_left + tileSize
            y_bottom = y_top  - tileSize

            # Skip anchors that would produce a partial tile outside raster
            if (x_left < src_left) or (x_right > src_right) or (y_bottom < src_bottom) or (y_top > src_top):
                continue

            # pass (0,0,left,top,0,0) → ensures process_tile uses left/top as-is
            tile_info_list.append((0, 0, x_left, y_top, 0.0, 0.0))

    process_tile_partial = partial(
        process_tile,
        pathToRaster=pathToRaster,
        outputPath=outputPath,
        crs=crs,
        tileSize=tileSize,
        res=res,
        datatype=dataType
    )

    with multiprocessing.Pool(num_workers) as pool:
        results = pool.map(process_tile_partial, tile_info_list)

    return results

def findIntTiles(metadataPath, lidarShapePath, epsg):
    tiles = []

    # Load the lidar shapefile
    lidar_shape = gpd.read_file(lidarShapePath)

    # Check the CRS
    target_crs = CRS.from_epsg(int(epsg))
    if lidar_shape.crs != target_crs:
        print(f"Reprojecting from {lidar_shape.crs} to EPSG:{epsg}")
        lidar_shape = lidar_shape.to_crs(target_crs)
    else:
        print(f"Shapefile is already in EPSG:{epsg}")

    # Get the geometry of the shapefile
    lidar_geometry = lidar_shape.geometry.unary_union

    # Load metadata
    with open(metadataPath, 'r') as f:
        metadata = json.load(f)

    # Check each metadata tile for intersection with the shapefile geometry
    for tile_id, tile_data in metadata.items():
        tile_minx = tile_data["min_x"]
        tile_maxx = tile_data["max_x"]
        tile_miny = tile_data["min_y"]
        tile_maxy = tile_data["max_y"]
        print(f'Tile {tile_id} bounds: {tile_minx}, {tile_miny}, {tile_maxx}, {tile_maxy}')

        # Create a box geometry for the tile
        tile_box = box(tile_minx, tile_miny, tile_maxx, tile_maxy)

        # Check if the tile intersects with the shapefile geometry
        if lidar_geometry.intersects(tile_box):
            tiles.append(tile_id)

    return tiles

def resolveOverlaps(wvimgInfPath, metadataPath):
    # Load metadata
    with open(metadataPath, 'r') as f:
        metadata = json.load(f)

    # Create a list of tiles with their geometries and dates
    tiles = []
    for tile_id, tile_data in metadata.items():
        tile_box = box(tile_data['min_x'], tile_data['min_y'], tile_data['max_x'], tile_data['max_y'])
        tile_date = datetime.strptime(tile_data['date'], '%Y-%m-%d')
        tiles.append((tile_id, tile_box, tile_date, tile_data['filePath']))

    # Find pairs of tiles that overlap
    for tile1, tile2 in combinations(tiles, 2):
        if tile1[1].intersects(tile2[1]):
            # Determine which tile is newer
            if tile1[2] > tile2[2]:
                newer_tile, older_tile = tile1, tile2
            else:
                newer_tile, older_tile = tile2, tile1

            # Calculate the difference between the older tile and the newer tile
            difference = older_tile[1].difference(newer_tile[1])

            # If there's a difference (i.e., the older tile is not completely covered)
            if not difference.is_empty:
                # Prepare the gdalwarp command
                input_file = os.path.join(wvimgInfPath, older_tile[3])
                
                # Create a temporary file in the same directory
                output_file = input_file + '_temp.tif'
                
                # Create a WKT string for the difference geometry
                wkt = difference.wkt
                
                # Construct the gdalwarp command
                command = [
                    'gdalwarp',
                    '-cutline', wkt,
                    '-crop_to_cutline',
                    '-overwrite',
                    input_file,
                    output_file
                ]

                # Execute the gdalwarp command
                try:
                    subprocess.run(command, check=True)
                    print(f"Successfully cropped {older_tile[0]}")
                    
                    # Replace the original file with the cropped version
                    os.remove(input_file)
                    os.rename(output_file, input_file)
                    print(f"Replaced original file for {older_tile[0]}")
                except subprocess.CalledProcessError as e:
                    print(f"Error cropping {older_tile[0]}: {e}")
                    # Clean up the temporary file if an error occurred
                    if os.path.exists(output_file):
                        os.remove(output_file)
                except OSError as e:
                    print(f"Error replacing file for {older_tile[0]}: {e}")
                    # Clean up the temporary file if an error occurred
                    if os.path.exists(output_file):
                        os.remove(output_file)


def renameTiles(ms_data_path):
    wvimg_path = os.path.join(ms_data_path, "wvimg")
    dem_path = os.path.join(ms_data_path, "DEM")
    lidar_path = os.path.join(ms_data_path, "chm")

    # Helper to rename or symlink tiles in target_dir based on wvimg
    def process_against_wvimg(target_dir):
        for wvimg_file in os.listdir(wvimg_path):
            if '_' not in wvimg_file:
                print('_ not in wvimg_file')
                continue

            tile_id, rest = wvimg_file.split('_', 1)
            reference_name = f"{tile_id}_{rest}"
            # Find matching tiles in DEM or lidar that include the tile_id
            matches = [f for f in os.listdir(target_dir) if rest in f]

            for match in matches:
                match_path = os.path.join(target_dir, match)

                if not os.path.isfile(match_path):
                    continue

                underscore_count = match.count('_')

                # If not renamed: do so
                if underscore_count == 1:
                    new_name = f"{tile_id}_{match}"
                    new_path = os.path.join(target_dir, new_name)
                    os.rename(match_path, new_path)

                # If already renamed: make symlink to avoid duplicates
                elif underscore_count >= 2:
                    existing_file = match_path
                    base_name = '_'.join(match.split('_')[1:])
                    symlink_name = os.path.join(target_dir, f"{tile_id}_{base_name}")
                    if not os.path.exists(symlink_name):
                        # Create relative symlink
                        link_target = os.path.relpath(existing_file, os.path.dirname(symlink_name))
                        os.symlink(link_target, symlink_name)

    # Process DEM and lidar using wvimg as reference
    process_against_wvimg(dem_path)
    process_against_wvimg(lidar_path)

    # # Clean up any files in DEM and lidar that don't have exactly 2 underscores
    # for cleanup_dir in [dem_path, lidar_path]:
    #     for fname in os.listdir(cleanup_dir):
    #         full_path = os.path.join(cleanup_dir, fname)
    #         if os.path.isfile(full_path) and fname.count('_') != 2:
    #             os.remove(full_path)

def makeLists(base_dir: str, site):
    # Define the subdirectories
    # subdirs = ['DEM', 'wvimg', 'lidar']
    subdirs = ['DEM', 'chm', 'wvimg']
    
    # Get the set of files for each subdirectory
    file_sets = []
    for subdir in subdirs:
        path = os.path.join(base_dir, subdir)
        if os.path.isdir(path):
            files = set(f for f in os.listdir(path) 
                        if f.lower().endswith('.tif') and not f.lower().endswith('.tif.aux.xml'))
            file_sets.append(files)
    
    # Find the intersection of all file sets
    common_files = set.intersection(*file_sets)
    
    # Convert to list and shuffle
    common_files_list = list(common_files)
    print(f'size of set intersection: {len(common_files_list)}')
    random.shuffle(common_files_list)
    
    # Calculate split sizes
    total_files = len(common_files_list)
    train_size = int(0.7 * total_files)
    val_size = int(0.15 * total_files)
    
    # Split the files
    train_files = common_files_list[:train_size]
    val_files = common_files_list[train_size:train_size+val_size]
    test_files = common_files_list[train_size+val_size:]
    
    # Write to output files
    write_to_file(train_files, os.path.join(base_dir, f'{site}_trainlist.txt'))
    write_to_file(val_files, os.path.join(base_dir, f'{site}_vallist.txt'))
    write_to_file(test_files, os.path.join(base_dir, f'{site}_testlist.txt'))

def write_to_file(file_list: List[str], output_file: str):
    with open(output_file, 'w') as f:
        for file_name in file_list:
            f.write(f"{file_name}\n")

def get_max_difference_in_dir(tif_dir):
    max_diff = -np.inf
    max_file = None

    for filename in os.listdir(tif_dir):
        if filename.lower().endswith(".tif"):
            filepath = os.path.join(tif_dir, filename)
            try:
                with rasterio.open(filepath) as src:
                    data = src.read(1, masked=True)
                    if data.mask.all():
                        continue
                    local_max = data.max()
                    local_min = data.min()
                    diff = local_max - local_min
                    if diff > max_diff:
                        max_diff = diff
                        max_file = filename
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    return max_diff, max_file


def normalize_and_save_tile(src_path, dst_path, global_max_range):
    with rasterio.open(src_path) as src:
        profile = src.profile
        data = src.read(1, masked=True)

        if data.mask.all():
            return None, None

        local_min = data.min()
        local_max = data.max()
        local_range = local_max - local_min
        midpoint = (local_min + local_max) / 2.0

        # Each pixel is shifted based on deviation from midpoint
        scale = 127.0 / (global_max_range / 2.0)  # 127 steps from midpoint to either edge

        # Shift values so midpoint = 128
        pixel_data = 128 + ((data - midpoint) * scale)

        # Clip and convert to uint8
        pixel_data = np.clip(pixel_data, 0, 255).astype(np.uint8)

        # Update profile for uint8 image
        profile.update(dtype=rasterio.uint8, count=1, nodata=0)

        with rasterio.open(dst_path, 'w', **profile) as dst:
            dst.write(pixel_data.filled(0), 1)

        return local_range, os.path.basename(dst_path)
    

def normDEMs(src_path, dst_path):
    global_max_range, max_range_file = get_max_difference_in_dir(src_path)

    for filename in os.listdir(src_path):
        if filename.lower().endswith(".tif"):
            src_tif_path = os.path.join(src_path, filename)
            dst_tif_path = os.path.join(dst_path, filename)
            try:
                diff, norm_file = normalize_and_save_tile(src_tif_path, dst_tif_path, global_max_range)
            except Exception as e:
                print(f"Error normalizing {filename}: {e}")

def findLidarResources(
    train_shp: str | Path,
    catalog_geojson: str | Path | dict,
    return_full: bool = False,
    verbose: bool = False
) -> List[Union[str, Dict[str, Any]]]:
    """
    Search a catalog GeoJSON (FeatureCollection) for resources whose
    geometries intersect the AOI. No name/state filtering is applied.

    Parameters
    ----------
    train_shp : path to AOI vector (any format readable by GeoPandas)
    catalog_geojson : path to the catalog GeoJSON *or* an already-loaded dict
    return_full : if True, return list of dicts with name/url/id/count/bounds; else list of URLs
    verbose : print a few debug lines

    Returns
    -------
    List[str]            (URLs)                     if return_full=False (default)
    List[Dict[str, Any]] (name/url/id/count/bounds) if return_full=True
    """

    # --- 1) Load AOI and normalize to EPSG:4326
    aoi = gpd.read_file(train_shp)
    if aoi.crs is None:
        raise ValueError("AOI has no CRS defined. Set it (aoi.set_crs) before running.")
    aoi_4326 = aoi.to_crs(4326)
    aoi_union = aoi_4326.union_all() if hasattr(aoi_4326, "union_all") else aoi_4326.unary_union

    # --- 2) Load the catalog GeoJSON (path or preloaded dict)
    if isinstance(catalog_geojson, (str, Path)):
        with open(catalog_geojson, "r") as f:
            obj = json.load(f)
    elif isinstance(catalog_geojson, dict):
        obj = catalog_geojson
    else:
        raise TypeError("catalog_geojson must be a path or a dict-like object.")

    if not isinstance(obj, dict) or obj.get("type") != "FeatureCollection":
        raise ValueError("Catalog must be a GeoJSON FeatureCollection.")

    feats = []
    for ft in obj.get("features", []):
        geom = ft.get("geometry")
        props = ft.get("properties", {}) or {}
        if not geom:
            continue
        try:
            shp = shape(geom)
            if shp.is_empty:
                continue
            feats.append({
                "name": props.get("name"),
                "url": props.get("url"),
                "id": props.get("id"),
                "count": props.get("count"),
                "geometry": shp
            })
        except Exception:
            # skip malformed features
            continue

    if not feats:
        return []

    gdf = gpd.GeoDataFrame(feats, geometry="geometry", crs=4326)

    # --- 3) Spatial prefilter via bbox index, then exact intersects
    try:
        idx = gdf.sindex.query(aoi_union, predicate="intersects")
        candidates = gdf.iloc[idx]
    except Exception:
        # fallback without spatial index
        aoi_bbox_poly = box(*aoi_union.bounds)
        candidates = gdf[gdf.intersects(aoi_bbox_poly)]

    hits = candidates[candidates.intersects(aoi_union)]
    if hits.empty:
        return []

    if verbose:
        print(f"AOI bounds: {aoi_union.bounds}")
        print(f"Found {len(hits)} intersecting resources in catalog.")
        print(hits[["name", "url"]].head())

    if return_full:
        out = []
        for _, r in hits.iterrows():
            minx, miny, maxx, maxy = r.geometry.bounds
            out.append({
                "name": r["name"],
                "url": r["url"],
                "id": r["id"],
                "count": r["count"],
                "bounds": (minx, miny, maxx, maxy),
            })
        return out

    # default: list of URLs (strings)
    return hits["url"].dropna().tolist()

def genTileAnchors(
    shp_path: str,
    spacing: int = 224,
    target_epsg: int | None = None,
    include_boundary: bool = True
) -> pd.DataFrame:
    """
    Create a grid of snapped points (multiples of `spacing`) within a polygonal area.

    Parameters
    ----------
    shp_path : str
        Path to the .shp file. Geometry must be polygonal (Polygon/MultiPolygon).
    spacing : int, optional
        Grid spacing in the same units as the CRS (meters for UTM). Default is 224.
    target_epsg : int | None, optional
        If provided, the shapefile will be reprojected to this EPSG before gridding.
        (e.g., 32617 for UTM zone 17N)
    include_boundary : bool, optional
        If True, include points on the boundary; otherwise strictly interior.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ["X", "Y"] containing grid points inside the shape.
    """
    # Load
    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        return pd.DataFrame(columns=["X", "Y"])

    # Reproject if requested
    if target_epsg:
        gdf = gdf.to_crs(epsg=target_epsg)

    # Guard against geographic CRS
    if gdf.crs is None or getattr(gdf.crs, "is_geographic", False):
        raise ValueError(
            "Input must be in a projected CRS (meters). "
            "Use target_epsg (e.g., 32617) or reproject your data before calling."
        )

    # Union to a single geometry (handles MultiPolygons and multiple rows)
    geom = gdf.unary_union
    if geom.is_empty:
        return pd.DataFrame(columns=["X", "Y"])

    # Bounding box aligned to the spacing grid (i.e., multiples of `spacing`)
    minx, miny, maxx, maxy = geom.bounds
    x0 = int(np.ceil(minx / spacing)) * spacing
    x1 = int(np.floor(maxx / spacing)) * spacing
    y0 = int(np.ceil(miny / spacing)) * spacing
    y1 = int(np.floor(maxy / spacing)) * spacing

    if x1 < x0 or y1 < y0:
        return pd.DataFrame(columns=["X", "Y"])

    xs = np.arange(x0, x1 + spacing / 2.0, spacing)
    ys = np.arange(y0, y1 + spacing / 2.0, spacing)

    # Mesh → coords
    X, Y = np.meshgrid(xs, ys)
    coords = np.column_stack((X.ravel(), Y.ravel()))

    # Build points (GeoSeries) with the same CRS
    pts = gpd.GeoSeries(gpd.points_from_xy(coords[:, 0], coords[:, 1]), crs=gdf.crs)

    # Predicate: include boundary via `covers` if available, else within|touches
    mask = None
    try:
        # shapely>=2 vectorized op
        import shapely
        if hasattr(shapely, "covers"):
            mask = shapely.covers(geom, pts.array) if include_boundary else shapely.contains(geom, pts.array)
    except Exception:
        pass

    if mask is None:
        # Fallback for older stacks using GeoPandas predicates
        if include_boundary:
            mask = pts.within(geom) | pts.touches(geom)
        else:
            mask = pts.within(geom)

    inside = coords[mask]

    # Return as requested
    df = pd.DataFrame(inside, columns=["X", "Y"])
    return df




def generate_chm_tiles(
    epsg: int,
    ept_urls: Iterable[str],
    points_df: pd.DataFrame,
    output_dir: str,
    r_script_path: str,  # kept in signature, but unused in LAZ-only mode
) -> None:
    """
    LAZ-only mode: fetches .laz files into output_dir/_laz_tmp and stops.
    No CHM GeoTIFF generation. Returns nothing.
    """

    START_DATE = "2000-01-01"
    END_DATE   = "2025-01-01"

    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    tmp_laz_dir = os.path.join(output_dir, "_laz_tmp")
    os.makedirs(tmp_laz_dir, exist_ok=True)

    num_cores = multiprocessing.cpu_count()
    num_workers = max(1, num_cores - 2)
    # print(f"Running with {num_workers} workers")

    def _normalize_url(u: str) -> str:
        return u if u.startswith("http") else f"https://{u}"
    ept_urls = [_normalize_url(u) for u in ept_urls]

    # Not needed in LAZ-only mode, but harmless to keep:
    def expected_tif_path(x, y):
        return os.path.join(output_dir, f"{int(x)}_{int(y)}.tif")

    def choose_laz(laz_candidates: Dict[str, str]) -> str:
        if len(laz_candidates) == 1:
            return next(iter(laz_candidates.values()))
        return sorted(laz_candidates.items(), key=lambda kv: kv[0])[-1][1]

    def process_point(row: Dict) -> None:
        x, y = float(row["X"]), float(row["Y"])
        laz_candidates: Dict[str, str] = {}
        print(f"[START] Point ({x:.2f}, {y:.2f})")

        for ept in ept_urls:
            try:
                laz_path = laz(  # <- your PDAL-based fetcher
                    x=x, y=y, epsg=epsg,
                    collect_start=START_DATE, collect_end=END_DATE,
                    url=ept, out_dir=tmp_laz_dir
                )
                size = os.path.getsize(laz_path)
                if size > 3 * 1024:
                    laz_candidates[ept] = laz_path
                    print(f"[FETCHED] {os.path.basename(laz_path)} ({size} bytes)")
                else:
                    os.remove(laz_path)
                    print(f"[EMPTY] Removed {os.path.basename(laz_path)}")
            except Exception as e:
                print(f"[ERROR] Fetch failed at ({x:.2f}, {y:.2f}) from {ept}: {e}")
                pass

        if not laz_candidates:
            print(f"[SKIP] No valid LAZ for ({x:.2f}, {y:.2f})")
            return

        # Choose one LAZ and then STOP (no R, no cleanup)
        laz_path = choose_laz(laz_candidates)
        out_tif = expected_tif_path(x, y)  # <- not needed in LAZ-only mode

        # ===== LAZ-ONLY: comment out the entire R subprocess block =====
        try:
            # print('Attempting to run Rscript')
            proc = subprocess.run(
                ['Rscript', r_script_path, laz_path, str(epsg), output_dir],
                 text=True, check=False, stdout=sys.stdout, stderr=sys.stderr
            )
            # print('Ran Rscript')
            if proc.stdout.strip():
                # print(f"[R STDOUT] ({int(x)},{int(y)}): {proc.stdout.strip()}")
                pass
            if proc.stderr.strip():
                # print(f"[R STDERR] ({int(x)},{int(y)}): {proc.stderr.strip()}")
                pass
        finally:
            # ===== LAZ-ONLY: comment out the cleanup so LAZ files remain =====
            for p in laz_candidates.values():
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception as ce:
                    print(f"[WARN] Could not remove {p}: {ce}")
                    pass
        print(f"[DONE] Point ({x:.2f}, {y:.2f})")
        return  # nothing to return

    # ===== IMPORTANT: UNCOMMENT the executor so it actually runs =====
    records = points_df[['X','Y']].to_dict(orient='records')
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futures = [ex.submit(process_point, r) for r in records]
        for fut in as_completed(futures):
            fut.result()  # surface exceptions
    return None


def laz(x, y, epsg, collect_start, collect_end, url, out_dir=".", buf=20.0, tile_size=256.0, resolution=1):
    """
    Fetch a buffered LAZ for a 256x256 m tile whose UPPER-LEFT is (x, y) in UTM.

    Steps:
      1) Build the exact UTM tile extent: [x, x+256] × [y-256, y]
      2) Project to EPSG:3857 and BUFFER by `buf` meters for the EPT read
      3) Reproject points to UTM
      4) Crop in UTM to the tile extent **buffered** by `buf` (keep neighbors)
      5) Write a .laz to `out_dir` and RETURN its absolute path

    Notes:
      - `collect_start` / `collect_end` kept for signature compatibility (not used by PDAL/EPT).
      - `buf` should be ≥ the largest neighborhood radius used by your CHM algorithm (e.g., 20–30 m).
    """
    # CRS strings
    utm     = f"EPSG:{epsg}"  # WGS84 / UTM north
    ept_crs = "EPSG:3857"
    # print('Entered LAZ')

    # Exact UTM tile bounds (this is the final tile footprint)
    tile_utm = box(x, y - tile_size, x + tile_size, y)
    # Buffered UTM polygon to keep neighbors for CHM computation
    tile_utm_buf = gpd.GeoSeries([tile_utm], crs=utm).buffer(buf).iloc[0]

    # Buffer AFTER projecting the exact tile to EPSG:3857 for the EPT reader
    tile_3857 = (
        gpd.GeoSeries([tile_utm], crs=utm)
        .to_crs(ept_crs)
        .buffer(buf)
        .iloc[0]
    )

    # Output file path (include a site name parsed from the EPT URL)
    site_name = os.path.basename(os.path.dirname(urlparse(url).path)) or "ept"
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.abspath(os.path.join(out_dir, f"{int(x)}_{int(y)}_{site_name}.laz"))

    # PDAL pipeline
    pipeline = {
        "pipeline": [
            {
                "type": "readers.ept",
                "filename": str(url),
                "polygon": tile_3857.wkt,  # buffered polygon in EPSG:3857
                "resolution": resolution
            },
            {
                # exclude Withheld (7) and Noise (18)
                "type": "filters.range",
                "limits": "Classification![7:7],Classification![18:18]"
            },
            {
                # reproject all points to UTM zone
                "type": "filters.reprojection",
                "out_srs": utm
            },
            {
                # crop in UTM to the BUFFERED tile (keep neighbors for edge cells)
                "type": "filters.crop",
                "polygon": tile_utm_buf.wkt
            },
            {
                "type": "writers.las",
                "compression": "laszip",
                "filename": filename
            }
        ]
    }

    # print('Executing pipeline')
    # Execute (streaming keeps memory usage reasonable)
    pdal.Pipeline(json.dumps(pipeline)).execute_streaming(chunk_size=1_000_000)
    # print('Finished pipeline execution')

    return filename

def createLidarData(train_shp, catalog_geojson, epsg, lidarTilesPath, anchors):
    # find intersecting lidar scan(s)

    lidarScans = findLidarResources(train_shp, catalog_geojson)
    print(f'lidarScans: {lidarScans}')

    # download lidar tifs
    pathToRScript = os.path.join(os.getcwd(), 'Rutils.R')
    generate_chm_tiles(epsg=epsg, ept_urls=lidarScans, points_df=anchors, output_dir=lidarTilesPath, r_script_path=pathToRScript)

def merge_chm_tiles(
    input_folder: str,
    output_tif: str,
    b: float = 16.0,      # meters: feather fully "on" by b meters from an edge
    c: float = 4.0,       # meters: fully "off" within c meters of an edge
    nodata: float = -9999 # output nodata
):
    """
    Merge georeferenced CHM tiles with edge feathering:
      - weight = 0 for pixels within c meters of any tile edge
      - weight ramps linearly 0→1 between c and b meters from the edge
      - weight = 1 for pixels ≥ b meters from every edge
    Overlaps are blended by weighted mean.

    Assumes all inputs share CRS and pixel size (square pixels).
    """
    tif_paths = sorted(glob(os.path.join(input_folder, "*.tif")))
    if not tif_paths:
        raise ValueError(f"No GeoTIFFs found in {input_folder}")

    # Read base metadata
    with rasterio.open(tif_paths[0]) as ds0:
        crs = ds0.crs
        resx = abs(ds0.transform.a)
        resy = abs(ds0.transform.e)
        if not np.isclose(resx, resy):
            raise ValueError("Non-square pixels not supported.")
        px = resx  # meters per pixel

    # Validate consistency
    for p in tif_paths[1:]:
        with rasterio.open(p) as d:
            if d.crs != crs:
                raise ValueError(f"CRS mismatch: {p}")
            if not (np.isclose(abs(d.transform.a), resx) and np.isclose(abs(d.transform.e), resy)):
                raise ValueError(f"Resolution mismatch: {p}")

    # Union bounds
    def _bounds(path):
        with rasterio.open(path) as d:
            return d.bounds
    bounds_list = [_bounds(p) for p in tif_paths]
    minx = min(b.left for b in bounds_list)
    miny = min(b.bottom for b in bounds_list)
    maxx = max(b.right for b in bounds_list)
    maxy = max(b.top for b in bounds_list)

    width  = int(np.ceil((maxx - minx) / px))
    height = int(np.ceil((maxy - miny) / px))
    out_transform = from_origin(minx, maxy, px, px)

    sum_arr = np.zeros((height, width), dtype=np.float64)
    wsum_arr = np.zeros((height, width), dtype=np.float64)

    # Precompute denominator for ramp (avoid divide-by-zero)
    ramp_den = max(1e-6, (b - c))

    for path in tif_paths:
        with rasterio.open(path) as d:
            tile = d.read(1).astype(np.float64)

            # Map to output window
            win: Window = from_bounds(*d.bounds, transform=out_transform, width=width, height=height)
            win = win.round_offsets().round_lengths()
            r0, c0 = int(win.row_off), int(win.col_off)
            h, w = int(win.height), int(win.width)

            r1 = min(r0 + h, height)
            c1 = min(c0 + w, width)
            tile = tile[: (r1 - r0), : (c1 - c0)]

            th, tw = tile.shape

            # Distance-to-nearest-edge (in meters) at each pixel
            rr = np.minimum(np.arange(th), np.arange(th)[::-1])  # pixels to top/bottom
            cc = np.minimum(np.arange(tw), np.arange(tw)[::-1])  # pixels to left/right
            dist_edge_px = np.minimum(rr[:, None], cc[None, :]).astype(np.float64)
            dist_edge_m = dist_edge_px * px

            # Feathered weights: 0 (<=c), linear to 1 (>=b)
            w = (dist_edge_m - c) / ramp_den
            np.clip(w, 0.0, 1.0, out=w)

            # Respect source nodata if present
            if d.nodata is not None:
                w = np.where(tile == d.nodata, 0.0, w)

            # Accumulate
            sum_arr[r0:r1, c0:c1] += tile * w
            wsum_arr[r0:r1, c0:c1] += w

    # Final mosaic (weighted mean), else nodata
    out = np.full((height, width), nodata, dtype=np.float32)
    mask = wsum_arr > 0
    out[mask] = (sum_arr[mask] / wsum_arr[mask]).astype(np.float32)

    os.makedirs(os.path.dirname(output_tif), exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": height,
        "width": width,
        "crs": crs,
        "transform": out_transform,
        "compress": "lzw",
        "nodata": nodata,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(output_tif, "w", **profile) as dst:
        dst.write(out, 1)

    return output_tif

def merge_tiles_with_avg_height_feathered(
    input_folder: str,
    output_tif: str,
    threshold: float = 2.0,  # keep only pixels > threshold when computing each tile's average
    b: float = 16.0,         # meters: weight ramps up to 1 by this distance from edges
    c: float = 4.0,          # meters: completely discard within this distance of edges
    nodata: float = -9999.0, # output NoData
    exclude_edges_in_average: bool = True  # ignore the outer c m when computing per-tile averages
):
    """
    Build a mosaic where each tile is represented by its own average CHM height
    (computed over pixels > `threshold`). The per-tile constant images are
    feather-blended across overlaps using the same c→b ramp as before.

    If `exclude_edges_in_average` is True, pixels within `c` meters of any tile edge
    are NOT used when computing each tile's average (to avoid edge artifacts).
    """

    tif_paths = sorted(glob(os.path.join(input_folder, "*.tif")))
    if not tif_paths:
        raise ValueError(f"No GeoTIFFs found in {input_folder}")

    # Read base metadata
    with rasterio.open(tif_paths[0]) as ds0:
        crs = ds0.crs
        resx = abs(ds0.transform.a)
        resy = abs(ds0.transform.e)
        if not np.isclose(resx, resy):
            raise ValueError("Non-square pixels not supported.")
        px = resx  # meters per pixel

    # Validate consistency
    for p in tif_paths[1:]:
        with rasterio.open(p) as d:
            if d.crs != crs:
                raise ValueError(f"CRS mismatch: {p}")
            if not (np.isclose(abs(d.transform.a), resx) and np.isclose(abs(d.transform.e), resy)):
                raise ValueError(f"Resolution mismatch: {p}")

    # Union bounds
    def _bounds(path):
        with rasterio.open(path) as d:
            return d.bounds
    bounds_list = [_bounds(p) for p in tif_paths]
    minx = min(bd.left for bd in bounds_list)
    miny = min(bd.bottom for bd in bounds_list)
    maxx = max(bd.right for bd in bounds_list)
    maxy = max(bd.top for bd in bounds_list)

    width  = int(np.ceil((maxx - minx) / px))
    height = int(np.ceil((maxy - miny) / px))
    out_transform = from_origin(minx, maxy, px, px)

    # Accumulators for feather-blended mosaic of constant tiles
    sum_arr = np.zeros((height, width), dtype=np.float64)
    wsum_arr = np.zeros((height, width), dtype=np.float64)

    ramp_den = max(1e-6, (b - c))  # avoid div-by-zero

    for path in tif_paths:
        with rasterio.open(path) as d:
            tile = d.read(1).astype(np.float64)
            th, tw = tile.shape

            # Build mask for averaging: > threshold, not nodata, and (optionally) not in the outer c m ring
            avg_mask = (tile > threshold)
            if d.nodata is not None:
                avg_mask &= (tile != d.nodata)

            if exclude_edges_in_average and c > 0:
                rr = np.minimum(np.arange(th), np.arange(th)[::-1])
                cc = np.minimum(np.arange(tw), np.arange(tw)[::-1])
                dist_edge_px = np.minimum(rr[:, None], cc[None, :]).astype(np.float64)
                dist_edge_m = dist_edge_px * px
                avg_mask &= (dist_edge_m >= c)

            # Compute per-tile average height
            if not np.any(avg_mask):
                # No valid data > threshold: skip this tile entirely
                continue
            tile_avg = float(tile[avg_mask].mean())

            # Create a constant-image tile filled with tile_avg
            const_tile = np.full_like(tile, tile_avg, dtype=np.float64)

            # Feathering weights for blending this tile into the mosaic
            rr = np.minimum(np.arange(th), np.arange(th)[::-1])
            cc = np.minimum(np.arange(tw), np.arange(tw)[::-1])
            dist_edge_px = np.minimum(rr[:, None], cc[None, :]).astype(np.float64)
            dist_edge_m = dist_edge_px * px
            w = (dist_edge_m - c) / ramp_den
            np.clip(w, 0.0, 1.0, out=w)

            # Respect source nodata: give weight 0 where nodata OR <= threshold (optional)
            # (We generally let the whole tile contribute, but you could zero out <=threshold if desired.)
            if d.nodata is not None:
                w = np.where(tile == d.nodata, 0.0, w)

            # Map to output window
            win: Window = from_bounds(*d.bounds, transform=out_transform, width=width, height=height)
            win = win.round_offsets().round_lengths()
            r0, c0 = int(win.row_off), int(win.col_off)
            h, w_cols = int(win.height), int(win.width)
            r1, c1 = min(r0 + h, height), min(c0 + w_cols, width)

            const_tile = const_tile[: (r1 - r0), : (c1 - c0)]
            w = w[: (r1 - r0), : (c1 - c0)]

            # Accumulate
            sum_arr[r0:r1, c0:c1] += const_tile * w
            wsum_arr[r0:r1, c0:c1] += w

    # Final blended mosaic
    out = np.full((height, width), nodata, dtype=np.float32)
    mask = wsum_arr > 0
    out[mask] = (sum_arr[mask] / wsum_arr[mask]).astype(np.float32)

    os.makedirs(os.path.dirname(output_tif), exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": height,
        "width": width,
        "crs": crs,
        "transform": out_transform,
        "compress": "lzw",
        "nodata": nodata,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(output_tif, "w", **profile) as dst:
        dst.write(out, 1)

    return output_tif
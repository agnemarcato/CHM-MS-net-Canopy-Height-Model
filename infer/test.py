"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""

# chm-ms-net/infer/main1.py
from pathlib import Path
import sys
import tempfile

# Add the project root (the folder that contains `prepTrainInputs/`) to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import prepTrainInputs.main1Utils as utils
from ms_net.infer import run_inference
import shutil 
import os
# import geopandas as gpd
from dotenv import load_dotenv
import time

################### SETUP #################

# loading env variables
load_dotenv()
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
chmPath = os.getenv('chmPath')
chmReducedPath = os.getenv('chmReducedPath')
shpPath = os.getenv('shpPath')
epsg = int(os.getenv('epsg'))
site = os.getenv('site')
inferenceShpPath = os.getenv('inferenceShpPath')
customTrainShpPath = os.getenv('customTrainShpPath')
fp_path = os.getenv('fp_path')
openTopoAPIkey = os.getenv('openTopoAPIkey')
maxarAPIkey = os.getenv('maxarAPIkey')
customLidarTifPath = os.getenv('customLidarTifPath')
numTrainImages = int(os.getenv('numTrainImages'))
# TODO: Change this to be extracted directly from lidar data
NORM_CONST = 46

############### PATH DEFINITIONS ###############
inf_data_path = os.path.join(project_path, f'{site}_data')
pathToLidarResources = os.path.join(project_path, 'resources.geojson')
root, _ = os.path.splitext(inferenceShpPath) # Find inf shape as defined during training input prep
inf_shp_output_path = root + "_utm.geojson"
infAnchorsPath = os.path.join(project_path, 'chm-ms-net', 'downloads', site, 'infShape', f'{site}_infAnchors.csv')
lidarTilesPath = os.path.join(inf_data_path, 'chm')
DEM_download_path = os.path.join(project_path, 'chm-ms-net', 'downloads', site, 'dem', f'{site}_dem_INF_download.tif')
dem_UTM_path = os.path.join(project_path, 'chm-ms-net', 'downloads', site, 'dem', f'{site}_dem_INF_UTM.tif')
DEM_prenorm_tiles_path = os.path.join(inf_data_path, 'dem_prenorm')
DEM_tiles_path = os.path.join(inf_data_path, 'DEM')
pathToWvimg = os.path.join(project_path, 'chm-ms-net','downloads', site, 'wvimgInf')
prewvimgPath = os.path.join(inf_data_path, 'prewvimg')
metadataPath = os.path.join(project_path, 'chm-ms-net', 'downloads', site, 'metadata', 'DGTilesMetadata.json')
outputRasterPath = os.path.join(inf_data_path, 'INF_chm_pred_merged.tif')
croppedOutputRasterPath = os.path.join(inf_data_path, 'cropped_INF_chm_pred.tif')
pathToWeights = '' # fairbanks weights
# Optional, only needed if trying to compute CBH in treelist
rdsPath = None


# folder creations
os.makedirs(inf_data_path, exist_ok=True)
os.makedirs(DEM_tiles_path, exist_ok=True)
os.makedirs(DEM_prenorm_tiles_path, exist_ok=True)
os.makedirs(prewvimgPath, exist_ok=True)

################ RUN INFERENCE #######################

print('Running inference')
run_inference(
        data_path=inf_data_path,
        site=site,
        NORM_CONST=NORM_CONST,
        model_loc=pathToWeights,
        epsg_code=epsg,
        phase='test'
    )
print(f'Ran inference, tiles saved to {os.path.join(inf_data_path, 'chm_preds')}')

############### MERGE CHM TILES FOR PREDS ######################

print('Merging chm tiles')
utils.merge_chm_tiles(
    input_folder=os.path.join(inf_data_path, 'chm_preds'),
    output_tif=outputRasterPath,
)
print(f'Merged chm tiles, saved merged raster to {outputRasterPath}')

# ###### CROP CHM RASTER BACK TO ORIGINAL SHAPE ########
# print('Cropping predicted CHM tif back to original shape')
# utils.cropTif(inputTif=outputRasterPath, shp=inferenceShpPath, outputTif=croppedOutputRasterPath, epsg=epsg)
# print(f'Cropped CHM tif, saved to {croppedOutputRasterPath}')

############# GENERATE TREELIST FOR PREDS ####################

print('Generating treelist with cloud2trees. This will take a while...')
if rdsPath != None:
    utils.genTreelist(tifPath=outputRasterPath, projectPath=project_path, rdsPath=rdsPath, epsg=epsg, filename='preds_treelist.csv')
else:
    utils.genTreelist(tifPath=outputRasterPath, projectPath=project_path, epsg=epsg, filename='preds_treelist.csv')
print(f'Generated treelist, saved to {os.path.join(os.path.dirname(outputRasterPath), 'preds_treelist.csv')}')

############### MERGE CHM TILES FOR TRUE DATA ######################

# create virtual dir
chm_dir = Path(os.path.join(inf_data_path, 'chm'))
test_list = Path(os.path.join(inf_data_path, f'{site}_testlist.txt'))
pseudo_dir = Path(tempfile.mkdtemp(prefix="pseudo_chm_"))

# Create symlinks for only the files in your list
with open(test_list) as f:
    for line in f:
        filename = line.strip()
        src = chm_dir / filename
        dst = pseudo_dir / filename
        if src.exists():
            os.symlink(src, dst)

testCHMPath = os.path.join(inf_data_path, 'testCHMmerged.tif')

print('Merging chm tiles')
utils.merge_chm_tiles(
    input_folder=pseudo_dir,
    output_tif=testCHMPath,
)

print(f'Merged chm tiles, saved merged raster to {testCHMPath}')

############# GENERATE TREELIST FOR TRUE DATA ####################

print('Generating treelist with cloud2trees. This will take a while...')
if rdsPath != None:
    utils.genTreelist(tifPath=testCHMPath, projectPath=project_path, rdsPath=rdsPath, epsg=epsg, filename='true_treelist.csv')
else:
    utils.genTreelist(tifPath=testCHMPath, projectPath=project_path, epsg=epsg, filename='true_treelist.csv')
print(f'Generated treelist, saved to {os.path.join(os.path.dirname(outputRasterPath), 'true_treelist.csv')}')
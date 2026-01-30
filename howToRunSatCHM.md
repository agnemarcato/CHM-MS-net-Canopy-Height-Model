# SatCHM Setup and Usage Guide

This document walks through one-time setup, data preparation, model training, and inference for running **SatCHM**.

---

## 1. Account Creation and Setup (One-Time)

Create accounts at the following websites:

- **https://opentopography.org**
  - After creating your account, request an **API key**.  
    You will need this later in step 3.
- **https://pro.gegd.com**
  - This is the source of the Vantor (formerly known as Maxar) imagery. GEGD Pro is only available to US government users 

---

## 2. Clone the Repository

Create a directory for your project (this will be your **project path**), then clone the repository into it (this will be your **repo path**).

### Example


`project_path=/mnt/c/Users/zach/Desktop/canopy`

`repo_path=/mnt/c/Users/zach/Desktop/canopy/SatCHM`


---

## 3. Create a `.env` File

In the root of the repository, create a file named `.env` and paste the following:

```
site=
epsg=
openTopoAPIkey=""
inferenceShpPath=""

# OPTIONAL ARGS
# customTrainShpPath=""
# customLidarTifPath=""
```

Fill in your values for site, epsg, and openTopoAPIkey.

### Notes

- The inferenceShpPath can refer to either a shp or geojson file
- By default, the model will draw a square around your inference area and select surrounding tiles to train on.
- For some edge cases (e.g., coastal areas), a custom training area may be helpful. You may hand draw a custom area to select training data from, and modify customTrainShpPath
- By default, lidar data is sourced from **USGS 3DEP**.
  - To use a different lidar source, provide a CHM raster `.tif` and modify and uncomment customLidarTifPath.

Fill in all fields **except** `inferenceShpPath`, which will be completed in Step 5.

### Example `.env` File

```
site=caldor
epsg=32610
openTopoAPIkey="abcdefg12345"
inferenceShpPath="/mnt/c/Users/zach/Desktop/canopy/SatCHM/downloads/${site}/infShp/caldor_infShp.geojson"

# OPTIONAL ARGS
# customTrainShpPath="/mnt/c/Users/zach/Desktop/canopy/SatCHM/downloads/${site}/trainShp/harv_trainShp.geojson"
# customLidarTifPath="/mnt/c/Users/zach/Desktop/canopy/SatCHM/downloads/${site}/laz/harvard_laz/NEON_lidar-point-cloud-line/NEON/merged_CHM.tif"
```

---

## 4. Create an Inference Shapefile

Create or use an existing **shapefile or GeoJSON** defining the inference area.

- Save the file path to `inferenceShpPath` in your `.env` file

---

## 5. Prepare Training Inputs

### Build and Activate the Conda Environment

Navigate to:

`
project_path/SatCHM
`

Then run:

```
conda env create -f SatCHMenv.yml
conda activate SatCHMenv
```

---

### Run `main1.py`

From the `prepTrainInputs` directory:

```
python main1.py
```

Notes:
- Runtime: **1–2 hours**
- Lidar download is the main bottleneck
- Outputs will be written to:

`
project_path/{site}_data/
`

---

### Download Satellite Imagery from Vantor

You must download **cloud-free, snow-free Vantor imagery** with:

- Off-nadir angle **< 20°**
- Coverage spanning training and inference areas

For now, contact **zcrennen@lanl.gov** for assistance.

#### Imagery Alignment

- Training imagery → year reported by `main1.py`
- Inference imagery → year of interest

#### Order Parameters

```
Production Parameters = ORTHO-READY (STANDARD) OR2A
Output Bands = Pan
Output File Format = GeoTIFF
Bits Per Pixel = 8
DRA = On
Compression = DEFLATE
Projection = UTM
Kernel = MTF
```

Move imagery to:

- Training imagery:
`
downloads/wvimgTrain
`

- Inference imagery:
`
downloads/wvimgInf
`

---

### Run `main2.py`

From `prepTrainInputs`:

```
python main2.py
```

Outputs will be available at:

`
project_path/{site}_data/
`

---

## 6. Train the Model

Navigate to `ms_net` and run:

```
python train.py
```

### GPU Notes

- GPU will be used after initial dataloading
- Dataloading may be slow on large datasets

Optional GPU test:

```
python testGPU.py
```

Model weights will be saved to:

`
project_path/SatCHM/ms_net/lightning_logs/version_0/checkpoints/
`

Weights are saved every **10 epochs**, and the model will train for **1000 epochs**.  
Subsequent runs will increment `version_1`, `version_2`, etc.  
If the model has trained to completion without issues, your weights should be saved as **epoch-epoch=999.ckpt**.

---

## 7. Run Inference

Navigate to `infer` and run:

```
python main.py
```

- By default, the most recent weights are used
- To use an alternative weights file that isn't the most recent one, uncomment line 75 and specify the path

Inference outputs will be available at:

`
{site}_INF_data
`

The merged predicted CHM raster is:

`
INF_chm_pred_merged
`

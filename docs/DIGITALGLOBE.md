# Working with DigitalGlobe 🌍 


Our model uses sensor and solar angles from the satellite imagery metadata to predict canopy height. Therefore, the metadata needs to be recorded carefully. 

<br>

You will be first prompted to answer this question: 

<br>

``` 
Are you using DigitalGlobe? (Y/N):
``` 

<br>

After selecting **Y**, you will be provided with this information:


<br>

``` 
Are you using DigitalGlobe? (Y/N):
Y
You selected DigitalGlobe.
1. Ensure that you have a DigitalGlobe account set up and are able to download data.
2. Use the WKT bounding box file to download imagery from DigitalGlobe for area of interest (AOI).
3. See documentation (docs/DIGITALGLOBE.md) for more specific instructions about naming conventions and downloading imagery.


Now generating the WKT (Well-Known Text Script) to input into DigitalGlobe...

WKT inputs for DigitalGlobe:

POLYGON ((-119.92239870449977 38.56099176006651, -119.92239870449977 38.8897615652315, -120.6590520182522 38.8897615652315, -120.6590520182522 38.56099176006651, -119.92239870449977 38.56099176006651))

WKT saved to C:\Users\mia\Documents\caldor_run\site-polygons\wkt\caldor.txt

Has it been 24 hours and/or you received confirmation that your imagery order has been fufilled? (Y/N):

``` 
At this point, several files have been created and/or updated: WKTs, GeoJSONs, and site-metadata.csv.

```
└── site-polygons
    ├── geojson
    │   ├── caldor.geojson
    │ 
    ├── with_crs
    │   └── Caldor
    │       ├── caldor.cpg
    │       ├── caldor.dbf
    │       ├── caldor.prj
    │       ├── caldor.shp
    │       └── caldor.shx
    └── wkt
        ├── caldor.txt
       
``` 

DigitalGlobe cannot create a bounding box from a WKT that is greater than 10,000 km². Additionally, if you were to download imagery via HTTPs, .zip files will be corrupt if they are over 300 km². Therefore, if you have a larger area, we divide the entire into smaller bounding boxes for faster processing and to account for memory. Your directory may look like this, if that is the case.
```
└── site-polygons
    ├── geojson
    │   ├── Caldor_cell0.geojson
    │   └── Caldor_cell1.geojson
    ├── with_crs
    │   └── Caldor
    │       ├── caldor.cpg
    │       ├── caldor.dbf
    │       ├── caldor.prj
    │       ├── caldor.shp
    │       └── caldor.shx
    └── wkt
        ├── Caldor_cell0.txt
        └── Caldor_cell1.txt
``` 

- **.geojsons** can be used to visualize the bounding boxes in any GIS software
- **.wkts** are printed in the command line to copy directly into DigitalGlobe, but they are also saved in .txt files in the **wkt** folder in your **site-polygons directory**
- **site-metadata.csv** is updated if your bounding box is divided into smaller chunks
   - There will be a row that has the whole bounds preserved (original eastings and northings) and rows that contain the chunked bounds. Otherwise, it remains the same (seen below).


<br>
<div style="text-align:center">
  <h3>site-metadata.csv</h3>
  <table style="margin: 0 auto; border-collapse: collapse;" border="1">
    <tr>
      <th>name</th>
      <th>e0</th>
      <th>e1</th>
      <th>n0</th>
      <th>n1</th>
      <th>utm_code</th>
      <th>chunk_or_whole</th>
    </tr>
    <tr>
      <td>caldor</td>
      <td>703966.21</td>
      <td>766935.36</td>
      <td>4270659.34</td>
      <td>4309046.78</td>
      <td>EPSG:32610</td>
      <td>whole bounds</td>
    </tr>
  </table>
</div>

</br>
<br>


Then, you are also prompted with this question directly.

``` 
Has it been 24 hours and/or you received confirmation that your imagery order has been fufilled? (Y/N):
``` 
You may preemptively answer **N**, you will given a RuntimeError. You can rerun main and answer **Y** once you have input your metadata.

---

## Ordering imagery from DigitalGlobe

1.  After logging onto DigitalGlobe, click on the **Map** Icon in the top right-middle of your screen.

<br>

2. Click on **Enter WKT** and enter the WKT(s) from what is printed in the command line starting with POLYGON. These here:
``` 
WKT inputs for DigitalGlobe:

POLYGON ((-119.92239870449977 38.56099176006651, -119.92239870449977 38.8897615652315, -120.6590520182522 38.8897615652315, -120.6590520182522 38.56099176006651, -119.92239870449977 38.56099176006651))
``` 
 A red bounding box will appear and zoom in on your area of interest (AOI). It will now only show images that overlap that AOI.

<br>

3. Click on the **Pencil** icon, and select **Continue to Advanced Search**

<br>

4. Before browsing the images, go to the filter icon, in the top right of the side panel, select it and filter the **Off-Nadir Angle** to between 0 to 20 Degrees.

<br>

5. Now, you may start browsing the imagery. 
   - Prioritize imagery that is collected closest to the aquisition date of your lidar data.
   - You want images that have no clouds. They have a cloud detecting algorithm which they say can be filtered by (% of clouds in the image), but it is not effective. Try your best visually to select images without clouds.
   - You can get imagery from WV01, WV02, and WV03. There are SWIR (Short-Wave Infrared) satellite imagery and VNIR (Near-Infrared) options on the WV03 satellite. You can get imagery WV03-VNIR but not the WV03-SWIR as you cannot order those images as panchromatic.

<br>

6. Once you find an image that fits the parameters above, hit the **Select** button, so that it goes into your **Selected** tab. 
   - Prioritize selecting the fewest number of images that can fully cover the AOI. 


<br>


7. Now, record the angle metadata in the angle-metadata.csv located in {project_directory}/metadata directory. The path was given to you when you started the program:
``` 
Open this .CSV file for documenting angle metadata. Please keep this open as you proceed:

	 ~/caldor_run/metadata/angle-metadata.csv
``` 
 On DigitalGlobe, click on the **three horizontal lines** in the **Type** column for each image, and select **View Metadata**. You will need to fill out these fields in the CSV.
   - Name of the Site (lowercase)
   - Cell (if necessary, see below)
   - Date of Acquisition (in this format: YYYY-MM-DD)
   - Legacy Identifier (ID)
   - Sensor Name (i.e. wv01, wv02, wv03)
   - Sensor (Target) Azimuth
   - Off-Nadir Angle
   - Solar Elevation
   - Solar Azimuth 



### Certain Cases
(a) If you are using multiple WKTs (meaning that your bounding box was divided into several), please enter in the **cell** column the WKT index that you are using. After recording metadata for imagery selected from one cell, for subsequent cells, repeat steps 2 through 7 where you will select images and the record metadata for each image. Your metadata should look something like this.

<table style="margin: 0 auto; border-collapse: collapse;" border="1">
  <thead>
    <tr>
      <th>site</th>
      <th>cell</th>
      <th>date</th>
      <th>id</th>
      <th>sensor</th>
      <th>targetazimuth</th>
      <th>offnadir</th>
      <th>solarazimuth</th>
      <th>solarelevation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>caldor</td>
      <td>0</td>
      <td>2015-08-05</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>193.37</td>
      <td>14.0267</td>
      <td>339.093</td>
      <td>68.13</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>0</td>
      <td>2011-09-05</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>283.07</td>
      <td>11.37</td>
      <td>155.38</td>
      <td>56.09</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>0</td>
      <td>2017-06-14</td>
      <td>10200100605E2700</td>
      <td>wv01</td>
      <td>119.013</td>
      <td>13.10</td>
      <td>247.89</td>
      <td>60.69</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>1</td>
      <td>2016-08-24</td>
      <td>103001005C516200</td>
      <td>wv02</td>
      <td>316.14</td>
      <td>18.57</td>
      <td>143.18</td>
      <td>57.61</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>1</td>
      <td>2016-06-24</td>
      <td>102001004F090C00</td>
      <td>wv01</td>
      <td>100.26</td>
      <td>15.44</td>
      <td>247.05</td>
      <td>61.343</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>1</td>
      <td>2015-08-05</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>339.0929</td>
      <td>14.02</td>
      <td>193.37</td>
      <td>68.14</td>
    </tr>
  </tbody>
</table>

<br>

(b) If you are not using multiple WKTs, please leave **cell** column empty. Your metadata should look something like this.

<table style="margin: 0 auto; border-collapse: collapse;" border="1">
  <thead>
    <tr>
      <th>site</th>
      <th>cell</th>
      <th>date</th>
      <th>id</th>
      <th>sensor</th>
      <th>targetazimuth</th>
      <th>offnadir</th>
      <th>solarazimuth</th>
      <th>solarelevation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>caldor</td>
      <td></td>
      <td>2015-08-05</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>193.37</td>
      <td>14.0267</td>
      <td>339.093</td>
      <td>68.13</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td></td>
      <td>2011-09-05</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>283.07</td>
      <td>11.37</td>
      <td>155.38</td>
      <td>56.09</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td></td>
      <td>2017-06-14</td>
      <td>10200100605E2700</td>
      <td>wv01</td>
      <td>119.013</td>
      <td>13.10</td>
      <td>247.89</td>
      <td>60.69</td>
    </tr>
   
  </tbody>
</table>

<br>

(c) In a rare case, images will have the same site name, cell (if using), date of acquisition, and sensor, but different solar elevations, solar azimuth, sensor/target azimuth, off-nadir angles. If so, please record, your metadata like this if that is the case: **{sensor name}-{idx}**. The idx can be any number, but it needs to be unique for the site name, cell (if using), and date of acquisition that each row will represent a unique image.

<table style="margin: 0 auto; border-collapse: collapse;" border="1">
  <thead>
    <tr>
      <th>site</th>
      <th>cell</th>
      <th>date</th>
      <th>id</th>
      <th>sensor</th>
      <th>targetazimuth</th>
      <th>offnadir</th>
      <th>solarazimuth</th>
      <th>solarelevation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>caldor</td>
      <td>0</td>
      <td>2015-08-05</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>193.37</td>
      <td>14.0267</td>
      <td>339.093</td>
      <td>68.13</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>0</td>
      <td>2017-06-14</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>283.07</td>
      <td>11.37</td>
      <td>155.38</td>
      <td>56.09</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>0</td>
      <td>2017-06-14</td>
      <td>10200100605E2700</td>
      <td>wv01-2</td>
      <td>119.013</td>
      <td>13.10</td>
      <td>247.89</td>
      <td>60.69</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>1</td>
      <td>2016-08-24</td>
      <td>103001005C516200</td>
      <td>wv02</td>
      <td>316.14</td>
      <td>18.57</td>
      <td>143.18</td>
      <td>57.61</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>1</td>
      <td>2016-06-24</td>
      <td>102001004F090C00</td>
      <td>wv01</td>
      <td>100.26</td>
      <td>15.44</td>
      <td>247.05</td>
      <td>61.343</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>1</td>
      <td>2015-08-05</td>
      <td>1020010044833A00</td>
      <td>wv01</td>
      <td>339.0929</td>
      <td>14.02</td>
      <td>193.37</td>
      <td>68.14</td>
    </tr>
  </tbody>
</table>

<br>

7. In the **Selected** tab, add the image to the cart by clicking **three horizontal lines** and select **Add Image to Cart**. Select these parameters listed below.

   - <p><strong>Order Name:</strong><br>
      - Record the name of the order as follows based on the fields listed in the metadata:<br>
        <div style="text-align:center">
      <h3>{site}_{YYYY-MM-DD}_{sensor name}</h3><br>
      </div>
      - If you are using multiple WKTs, like in case (a):
      <div style="text-align:center"><br>
     <strong>caldor0_2017-06-14_wv01</strong>
     </div>
     <br>
      - If you are using one WKT, like in case (b):
      <div style="text-align:center"><br>
     <strong>caldor_2017-06-14_wv01</strong>
     </div>
     <br>
      - Include the sensor name recorded in the metadata for case (c):<div style="text-align:center"><br>
      <strong>caldor0_2017-06-14_wv01-2</strong>
      </div>
      </p>
      <br>
   - <p><strong>Deliver To:</strong> Library</p>

   - <p><strong>Product Type:</strong> Ortho Panchromatic</p>

   - <p><strong>Image File Format:</strong> GeoTiff</p>

   - <p><strong>Compression:</strong> Zip</p>

   - <p><strong>Clip Feature to AOI:</strong> YES, Clip to AOI</p>

<br>

8. Go to **Cart** at the top of the page, and click **Submit Order(s)** after you add ALL of your images to the cart. You will receive one email that gives confirmation that the order(s) were received and another email in about 12-24 hours that it is ready to download.

<br>

---

### Downloading the imagery through HTTPS
You can still download your imagery through HTTPs.

After you have received email confirmation that all your images have been fullfilled, go to DigitalGlobe and login. 

   - (1) On the top header, click on **My Imagery**
   - (2) Click on **Library**
   - (3) Now, you will see of your data listed one by one. Click on one & click on **Download**.
   - (4) Click on **Select** & you are given options on how you want to download. Choose **HTTPS**. 
   - (5) You will have repeat steps 3 and 4 for each file. 

<br>

<h4><em><span style="color:#06202B">Remember that .env file.</span></em></h4>

```
project_path=/Users/mia/Documents/Projects/caldor_run
site=caldor
utm=EPSG:32610
dem_path=/Users/mia/Documents/caldor_dem.tif
lidar_path=/Users/mia/Documents/caldor_lidar.tif
site_shapefile_dir=/Users/mia/Downloads/wgs84_caldor
satellite_download_dir= /Users/mia/Downloads/satellite_data
```
Download all of your imagery to the directory of **satellite_imagery_downloads_path**.

</br>

Afterwards, rerun the program. Enter **N** for the first prompt.

``` 
Are you using DigitalGlobe? (Y/N): N
``` 
You will immediately be prompted with this:

``` 
Please see the documentation for more specific instructions using your own satellite data.


Unpack your data into this directory:

	/Users/mia/Downloads/satellite_data
```
You do not need to unzip them. Leave them as .zip files. They will be processed appropriately from there. 

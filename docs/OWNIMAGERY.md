# Using your own Imagery 📷

#### Before proceeding to use your own imagery, you must answer **YES** to all these questions:
- Are your images panchromatic geotiffs?
    - Panchromatic means that they have one band. RGB images have three bands: R, G, B. You can easily convert RBG images to panchromatic using python.
    - In order for the images to be GeoTIFFs, they need to have spatial information associated with them. They should be able to be projected into a coordinate reference system (CRS).
    - They end with the extentsion: .tif or .tiff 
- Are your images high resolution?
    - The standard images that we use from DigitalGlobe are 50 to 60 centimeters. If you use images that have coarser resolution, the predictions of canopy height will then be coarser.
- Do you have angle metadata (solar azimuth, solar elevation, target/sensor azimuth, off-nadir angle) associated with every image?
    - One of the inputs to our model uses sensor and solar angles from the satellite imagery.
- Are the off-nadir angles for your images less than 20 degrees?
    - When there are higher off-nadir angles, there results in more foreshortening and distortion in the imagery and thus less accurate predictions

### Recording Metadata


``` 
Processing the satellite imagery...

Open this .CSV file for documenting angle metadata. Please keep this open as you proceed:

	 ~/{project_path}/metadata/angle-metadata.csv

```



You will be first prompted to answer this question: 

<br>

``` 
Are you using DigitalGlobe? (Y/N):
``` 

<br>

After selecting **N**, you will be provided with this information:


<br>

``` 
Are you using DigitalGlobe? (Y/N):
N


Please see the documentation for more specific instructions using your own satellite data.


Unpack your data into this directory:

{satellite_download_dir}

Press ENTER when complete:
``` 

### Filling out your metadata

You will group your images based on their **date of acquisition** and **sensor and solar angles**.

For example, you have a set of imagery for this site, caldor, and have its metadata.

![Alt text](/pictures/ownimagery.png)

### A : 
- Date of Acquisition: 2015-09-03
- Sensor/Target Azimuth: 165.5°
- Off-Nadir Angle: 6.3°
- Solar Azimuth: 124.1°
- Solar Elevation: 140.21°

### B : 
- Date of Acquisition: 2013-04-16
- Sensor/Target Azimuth: 142.4°
- Off-Nadir Angle: 7.8°
- Solar Azimuth: 65.9°
- Solar Elevation: 135.9°


### C : 
- Date of Acquisition: 2011-02-04
- Sensor/Target Azimuth: 141.2°
- Off-Nadir Angle: 4.1°
- Solar Azimuth: 154.3°
- Solar Elevation: 63.2°



Although there are two A blocks of images in different locations, they possess the same time/date of acquisition and angle metadata. Open the .CSV given to you and fill out the table as follows:


<table style="margin: 0 auto; border-collapse: collapse;" border="1">
  <thead>
    <tr>
      <th>site</th>
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
      <td>2015-09-03</td>
      <td></td>
      <td></td>
      <td>165.5</td>
      <td>6.3</td>
      <td>124.1</td>
      <td>140.21</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>2017-06-14</td>
      <td></td>
      <td></td>
      <td>142.4</td>
      <td>7.8</td>
      <td>65.9</td>
      <td>135.9</td>
    </tr>
    <tr>
      <td>caldor</td>
      <td>2017-06-14</td>
      <td></td>
      <td></td>
      <td>141.2</td>
      <td>4.1</td>
      <td>154.3</td>
      <td>63.2</td>
    </tr>
  </tbody>
</table>

<br>


Ignore the columns id and sensor. There should be three row entries because there are only three unique groups of satellite data (they have the same time/date of acquisition and angle metadata).

### Saving your data

   - Since you have **3 rows** enter in your metadata, you will have **3 folders** in your directory:

``` 
Unpack your data into this directory:

    {satellite_download_dir}


Press ENTER when complete:
``` 

- The name of the folder is based on the fields listed in the metadata for each collection images (with their unique dates of acquisition and angle metadata) saved in the directory provided above:<br>
        <div style="text-align:center">
      <h3>{site}_{YYYY-MM-DD}</h3><br>
      </div>

Therefore, it should look like this in your satellite_download_dir:
``` 

├── {satellite_download_dir}
│   ├── caldor_2011-02-04
│   ├── caldor_2013-04-16
│   └── caldor_2015-09-03

``` 
All of your GeoTIFF images should be saved in the appropriate folder. Then, the CHMer will process your data from there.
"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"""

This script is for processing the lidar data and digital elevation model (DEM) into 1010 x 1010 m tiles. Originally written by Chuck Abolt in Matlab, but edited and written by Mia Mitchell in Santa Fe, New Mexico. Fall 2024.

"""

import os
import subprocess
from shapely.geometry import box
import pandas as pd
import rasterio
import argparse
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv


def processAuxTifs(input_tif, output_directory):
    """
    Description
    ___________
    This is the main function for processing the lidar and DEM input files.

    Parameters
    __________
    input_tif : str
        The input .tif file being processed
    output_directory : str
        The output directory for the file being processed
    """
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    directory = os.getenv("project_path")

    metadata_path = os.path.join(directory, "metadata", "site-metadata.csv")
    metadata = pd.read_csv(metadata_path)
    chunks = []

    if "chunk bounds" in metadata["chunk_or_whole"].values:
        metadata = metadata[metadata["chunk_or_whole"] == "chunk bounds"]
    else:
        metadata = metadata[metadata["chunk_or_whole"] == "whole bounds"]

    for _, row in metadata.iterrows():
        name = row["name"]
        if name not in chunks:
            chunks.append(name)

    print("\nTotal chunks:", chunks)

    # get site data
    def getting_site_information(metadata_path, chunk):
        metadata = pd.read_csv(metadata_path)
        metadata = metadata.dropna(
            subset=["name", "e0", "e1", "n0", "n1", "utm_code", "chunk_or_whole"]
        )
        parsed = metadata[metadata["name"] == f"{chunk}"]
        name = f"{chunk}"
        e0, e1, n0, n1 = (
            parsed["e0"].iloc[0],
            parsed["e1"].iloc[0],
            parsed["n0"].iloc[0],
            parsed["n1"].iloc[0],
        )
        utmcode = parsed["utm_code"].iloc[0]
        return e0, e1, n0, n1, utmcode, name

    # get raster bbox
    def get_file_bbox(file_path):
        with rasterio.open(file_path) as src:
            bounds = src.bounds
        return bounds

    raster_bounds = get_file_bbox(input_tif)
    raster_geom = box(*raster_bounds)

    chunk_pbar = tqdm(chunks, desc="Processing chunks", unit="chunk")  
    for c in chunks:
        e0, e1, n0, n1, utmcode, name = getting_site_information(metadata_path, c)
        chunk_pbar.set_description(f"Working on site: {c}")
        eLL = range(int(e0), int(e1), 1000)
        nLL = range(int(n0), int(n1), 1000)
        total_iterations = len(eLL) * len(nLL)

        #print(f"\n\nOutput directory: {output_directory}\n\n")
        tile_pbar = tqdm(
            total=total_iterations,
            desc="Processing tiles",
            unit="tile",
            leave=False,
        )
        
        for e in eLL:
            for n in nLL:
                sqkm = str(e)[:3] + "_" + str(n)[:4]
                bbox_coords = [e - 10, n - 10, e + 1010, n + 1010]
                bbox_geom = box(*bbox_coords)
                bbox = " ".join(
                    [str(e - 10), str(n - 10), str(e + 1010), str(n + 1010)]
                )
                outfile = os.path.join(output_directory, f"{sqkm}.tif")

                tile_pbar.update(1)
                tile_pbar.set_description(
                    f"Processing easting={e}, northing={n}"
                )
                
                if raster_geom.intersects(bbox_geom):
                    outfile = os.path.join(output_directory, f"{sqkm}.tif")
                else:
                    #tile_pbar.write("Doesn't intersect...continuing...")
                    continue

                projcmd = (
                    f"rio warp {input_tif} {outfile} "
                    f"--dst-crs {utmcode} "
                    f"--bounds {bbox} "
                    "--resampling cubic "
                    "--res 0.5 "
                    "--overwrite"
                )

            
                result = subprocess.run(
                    projcmd.split(" "),
                    capture_output = True,
                    text = True 
                )
                if result.returncode != 0:
                    raise RuntimeError(f"\n\ncommand:\n\n\t>{projcmd}<\n\nFAILED with stdout:\n\n"
                                       f"{result.stdout}"
                                        "\n\nSTDERR:\n\n"
                                       f"{result.stderr}\n\n")
                
                if os.path.exists(outfile):
                    with rasterio.open(outfile) as src:
                        data = src.read(1)
                        nodata_value = src.nodata
                        if nodata_value is not None and np.all(
                            data == nodata_value
                        ):
                            os.remove(outfile)
                        else:
                            continue
                else:
                    tile_pbar.write("Continuing...")
        chunk_pbar.update(1)
    chunk_pbar.write(
            f"Finished creating 2020 x 2020 tiles for {os.path.split(input_tif)[-1]}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Projecting a GeoTIFF into 1010 x 1010 tiles')

    parser.add_argument('--input_tif', type=str, help='Path to the projected GeoTIFF')
    parser.add_argument('--output_directory', type=str, help='Path to the output directory for the the tiled GeoTIFFs')

    args = parser.parse_args()

    processAuxTifs(args.input_tif, args.output_directory)

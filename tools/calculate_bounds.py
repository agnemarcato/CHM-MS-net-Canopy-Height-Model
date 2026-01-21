"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"This calculates the bounds of wvimg files to apply them to the predicted chm outputs. It saves them in a .geojson. Written by Mia Mitchell in Los Alamos, NM. May 2025"
import os
import json
import rasterio
import argparse
from tqdm import tqdm

def calculating_wvimg_bounds(directory, output_json):
    """
    Description
    ___________
    Main function for this script

    Parameters
    __________
    directory : str
        the directory that contains the satellite images
    output_json : str
        the .json that will contain the filename and bounds of the satellite images

    """
    geotiff_bounds = {}

    def get_geotiff_bounds(directory, output_json):
        """
        Description
        ___________
        Function that calculates the bounds for the satellite images, saves their filenames, and corresponding bounds in a .json.

        Parameters
        __________
        directory : str
            the directory that contains the satellite images
        output_json : str
            the .json that will contain the filename and bounds of the satellite images

        """
        bounds_pbar = tqdm(os.listdir(directory), desc="Processing tiles", unit="tile", leave=True)

        for filename in os.listdir(directory):
            if filename.lower().endswith(('.tif', '.tiff')):
                filepath = os.path.join(directory, filename)
                try:
                    with rasterio.open(filepath) as src:
                        bounds = src.bounds
                        geotiff_bounds[filename] = {
                            'left': bounds.left,
                            'bottom': bounds.bottom,
                            'right': bounds.right,
                            'top': bounds.top
                        }
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                finally:
                    bounds_pbar.update(1)

    get_geotiff_bounds(directory, output_json)

    with open(output_json, 'w') as f:
        json.dump(geotiff_bounds, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculates the bounds of a GeoTIFF and saves them in a .json.')
    parser.add_argument('--directory', type=str, help='Path to the directory of the GeoTIFFs')
    parser.add_argument('--output_json', type=str, help='Path to output json file')
    args = parser.parse_args()
    calculating_wvimg_bounds(args.directory, args.output_json)

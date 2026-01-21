"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"""
This matches the names of inputs based on their base: {easting}_{northing}_{subdivision0}_{subdivision1}. Then, it proceeds to rename and/or files, so that that the length and names of inputs match appropriately. Written by Mia Mitchell in Santa Fe, New Mexico. Spring 2025.
"""

import os
import json
from collections import defaultdict
from dotenv import load_dotenv, find_dotenv
import argparse
import shutil

def matchKeys(data_type):
    """
    Description
    ___________

    This is the main function for correcting the names of files

    Returns
    _______

    paths : dict
     
    
    """
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    project_directory = os.getenv('project_path')
    output_json = os.path.join(project_directory, "inputs", f"{data_type}.json")

    wvimg = os.path.join(project_directory, "inputs", "wvimg")
    other_folder = os.path.join(project_directory, "inputs", data_type)  ######

    # Functions
    def collect_file_patterns(root_folder):
        """
        Description
        ___________
        This function collects file patterns from the files within the provided root folder and its subfolders.

        Parameters
        __________

        root_folder : str
            The path to the root folder to search for files.

        Returns
        _______
    
        file_patterns : (collections.defaultdict(set))
            A dictionary-like object that maps the file patterns
        """
        file_patterns = defaultdict(set)

        for root, _, files in os.walk(root_folder):
            for file in files:
                name, ext = os.path.splitext(file)
                parts = name.split("_")
                
                # Get the last 4 parts: they should be {easting}_{northing}_{subdivision0}_{subdivision1}
                if len(parts) >= 4:
                    key = "_".join(parts[-4:]) 
                    file_patterns[key].add(os.path.join(root, file))

        return file_patterns
    def compare_folders(folder1, folder2):
        """
        Description
        ___________

        This function compares two folders and identifies common file patterns
        present in both.

        Parameters
        __________

        folder1 : str
            The path to the first folder to be compared.
        folder2 : str
            The path to the second folder to be compared.

        Returns
        _______

        dict
            A dictionary where each key is a file pattern found in both folders,
            and the corresponding value is a tuple containing the pattern's value
            from folder1 and folder2 respectively.
    
        """
        patterns1 = collect_file_patterns(folder1)
        patterns2 = collect_file_patterns(folder2)

        common_patterns = {key: (patterns1[key], patterns2[key]) for key in patterns1 if key in patterns2}

        return common_patterns


    common_patterns = compare_folders(wvimg, other_folder)

    class SetEncoder(json.JSONEncoder): #saves this as a dictionary
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)  # convert sets to lists
            return super().default(obj)

    with open(output_json, "w") as f:
        json.dump(common_patterns, f, cls=SetEncoder, indent=4)
    print(f"Saved {data_type} mapping to {output_json}")
    print("Now to rename and create duplicates for ms-net..")


    with open(output_json, "r") as f:
        json_data = json.load(f)

    for key in json_data.keys(): #need to be a list for indexing
            #print("Starting with", key)
            wvimg_files, old_file = json_data[key]
            for wvimgfile in wvimg_files:
                basename = os.path.basename(wvimgfile)  
                #print("Processing...", basename)
                new_file = os.path.join(project_directory, "inputs", data_type, basename)  
                #print("New file path name:", new_file)
                oldf = old_file[0]
                if os.path.abspath(oldf) != os.path.abspath(new_file):
                    shutil.copy(oldf, new_file)  
                else:
                    continue
            


    if data_type == "dem":
        #print("Now to make sure the file list is identical")
        files1 = set(os.listdir(other_folder))
        files2 = set(os.listdir(wvimg))

        uniquetofolder1 = files1 - files2  
        uniquetofolder2 = files2 - files1 
        #print(len(files1) - len(uniquetofolder1) == len(files2) - len(uniquetofolder2))
        for file in uniquetofolder1:
            os.remove((os.path.join(other_folder,file)))
        for file in uniquetofolder2:
            os.remove((os.path.join(wvimg,file)))

    elif data_type == "chm":
        #print("Now to make sure the file list is identical")
        files1 = set(os.listdir(other_folder))
        files2 = set(os.listdir(wvimg))

        uniquetofolder1 = files1 - files2  
        for file in uniquetofolder1:
            os.remove((os.path.join(other_folder,file)))
    else:
        print("Incorrect data-type selected. Either chm or dem.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Match keys between two datasets.')
    parser.add_argument('data_type', type=str, choices=['dem', 'chm'], help='Type of data to be matched (either "dem" or "chm")')
    args = parser.parse_args()

    matchKeys(args.data_type)


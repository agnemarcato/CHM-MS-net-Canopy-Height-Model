"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"""
This creates the the training and validation .txt lists used for ms-net. Written by Mia Mitchell in Santa Fe, New Mexico. Spring 2025.
"""

import os
import random
from dotenv import load_dotenv, find_dotenv

def train_val_test_split():
    """
    Description
    ___________
    Main function for creating training, testing, and validation lists.
    """
    # Pulled from the .env 
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    project_directory = os.getenv('project_path')
    site = os.getenv('site')

    # Train-validation-test split (70 | 15 | 15)
    chm_files = set(os.listdir(os.path.join(project_directory, "inputs", "chm")))
    wvimg_files = set(os.listdir(os.path.join(project_directory, "inputs", "wvimg")))

    inference_files = sorted(wvimg_files - chm_files)
    with open(os.path.join(project_directory, "inputs", "inference_list.txt"), "w") as f:
        for name in inference_files:
            f.write(f"{name}\n")
    


    # File list
    random_seed = 2025 
    random.seed(random_seed)
    file_list = list(chm_files)
    random.shuffle(file_list)

    total_files = len(file_list)
    train_size = int(0.7 * total_files)
    val_size = int(0.15 * total_files)

    train_files = file_list[:train_size]
    val_files = file_list[train_size:train_size+val_size]
    test_files = file_list[train_size+val_size:]

    print(f"\nNumber of Training Images: {len(train_files)}")
    print(f"Number of Validation Images: {len(val_files)}")
    print(f"Number of Test Images: {len(test_files)}")
    print(f"Rest of Images (To Predict On Later): {len(inference_files)}\n")

    def save_list_to_file(file_list, filename):
        """
        Description
        __________

        This function saves filenames in the directory in a text file

        Parameters
        __________

        file_list : list
            the list of files in the directory
        filename : str
            the file name being added to the list
        
        """
        with open(filename, 'w') as f:
            for item in file_list:
                f.write(f"{item}\n")

    save_list_to_file(train_files, os.path.join(project_directory, "inputs", f"{site}_train.txt"))
    save_list_to_file(val_files, os.path.join(project_directory, "inputs", f"{site}_val.txt"))
    save_list_to_file(test_files, os.path.join(project_directory, "inputs", f"{site}_test.txt"))

if __name__ == "__main__":
    train_val_test_split()

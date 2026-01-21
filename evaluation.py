"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"This contains the scripts for evaluation. Written by Mia Mitchell"
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # only for Windows OS
from ms_net_architecture.infer import run_inference
from post_processing.treewise_evaluation import treewise_pixelwise_evaluation
from dotenv import load_dotenv, find_dotenv

# Loading the environment
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
project_directory = os.getenv("project_path")

# If you are infering on your test data
testresponse = input("Are you infering on your test data? (Y/N):")
if testresponse.upper() == 'Y':
    ckpt_path = input("Please enter the path to your model checkpoint file (found in lightning_logs) that you are satisified with (must end with '.ckpt'): ").strip().strip('"').strip("'")
    test_data = True
    if not ckpt_path.endswith(".ckpt"):
        raise ValueError("Invalid checkpoint path. The file must end with '.ckpt'.")
# If you are not infering on your test data
if testresponse.upper() == 'N':
    print("You will be infering on inputs that have no corresponding validation data.")
    ckpt_path = input("Please enter the path to your model checkpoint file (found in lightning_logs) that you are satisified with (must end with '.ckpt'): ").strip().strip('"').strip("'")
    test_data = False
    if not ckpt_path.endswith(".ckpt"):
        raise ValueError("Invalid checkpoint path. The file must end with '.ckpt'.")
    
model_loc = os.path.abspath(ckpt_path)

# Running inference
run_inference(model_loc, use_test_data = test_data)
print(f"Saved predicted CHM test outputs to {project_directory}/outputs/predicted_chms")
if test_data==True:
    print("Creating error figures for both pixelwise and tree approximate object (TAO) evaluation...")
    # Producing corresponding charts
    treewise_pixelwise_evaluation()
    print(f"Figures are saved in {project_directory}/outputs.")





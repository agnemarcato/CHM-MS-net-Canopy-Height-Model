"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"""
This makes predictions on your test data and sames them as GeoTIFFs. Predictions can be made on other lists of data that has the wvimg, solar, sensor, dem inputs. Written by Chuck Abolt and Mia Mitchell. Santa Fe, NM. Summer 2025.

"""

from .network_2D_lightning import MS_Net
from dotenv import load_dotenv, find_dotenv
import json
from .ms_parser import parse_args
from .pore_utils_2D import get_dataloader
import os
import torch
import rasterio

def run_inference(model_loc, use_test_data):
    """
    Description
    ___________
    Main function for running inference on test data and/or data without corresponding validation.

    Parameters
    __________
    use_test_data : bool
        if true, then the test data list is used, if not the data without corresponding validation data is used
    model_loc : str
        the path to the checkpoint
    """

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    directory = os.getenv('project_path')
    utm = os.getenv('utm')
    site = os.getenv('site')

    params = parse_args()

    # Training, testing, and inference lists (it says validation)
    params.train_list = os.path.join(directory, "inputs", f'{site}_train.txt') 
    
    if use_test_data==True:
        params.val_list = os.path.join(directory, "inputs", f'{site}_test.txt') 
        params.x_array = ['wvimg', 'solar', 'sensor', 'dem']
        params.y_array = ['chm']
    else:
        params.val_list = os.path.join(directory, "inputs", 'inference_list.txt') 
        params.x_array = ['wvimg', 'solar', 'sensor', 'dem']
        params.y_array = [] 

    params.x_xform = [None, None, None, None] 
    params.y_xform = [None]
    params.c_xform = [None]
    params.model_loc = 'chks'
    
    net_dict = vars(params) 
    
    net_dict['uz_stats'] = {}
    net_dict['uz_stats']['scalar'] = 1 # 5e-8 does not blow our grads
    
    net_dict['edist_stats'] = {}
    net_dict['edist_stats']['scalar'] = 2.7 # 500 does not blow our grads
    net_dict['c_stats'] = {}
    net_dict['c_stats']['scalar'] = 1 # 500 does not blow our grads
    net_dict['p_stats'] = {}
    net_dict['p_stats']['scalar'] = 0 
    net_dict['D_stats'] = {}
    net_dict['D_stats']['scalar'] = 0 
     
    model = MS_Net.load_from_checkpoint(model_loc,
                                    net_name     = 'MS-net',
                                    num_scales   = 3,
                                    num_features = 4,
                                    num_filters  = 2,
                                    f_mult       = 4)


    
    train_dataloader = get_dataloader(net_dict, ['train'])
    val_dataloader   = get_dataloader(net_dict, ['val'])
    
    traindata   = train_dataloader['train'].dataset
    valdata     = val_dataloader['val'].dataset



    predicted_chms_path = os.path.join(directory, "outputs", "predicted_chms")
    os.makedirs(predicted_chms_path, exist_ok=True)
    print("Creating test inference outputs...")
    for i in range(len(valdata)):
        sample, masks, xy = valdata[i]
        device = next(model.parameters()).device

        # Prepare input data
        x = [wvsam[None, :].to(device) for wvsam in xy[0]]
        masks = [mask.to(device) for mask in masks]

        # prediction
        model.eval()
        with torch.no_grad():  # disabling gradient computation during inference
            y_pred = model(x, masks)
        y_pred = [y_sub.detach().cpu() * 80 for y_sub in y_pred]  # multiply predicted values by 80 

        y_pred_np = y_pred[-1].cpu().numpy()[0, 0, :, :]

        # pull bounds from bounds.json
        with open(os.path.join(directory, "inputs", f'{site}_test.txt'), 'r') as file:
            entries = file.readlines()
        if i == range(len(valdata))[-1]:
            filename = entries[1]
        else: 
            filename = entries[i+1]
        filename = filename.strip()

        json_path = os.path.join(directory, "inputs", 'bounds.json')
        with open(json_path, 'r') as file:
            data = json.load(file)

        left = data[f"{filename}"]["left"]
        bottom = data[f"{filename}"]["bottom"]
        right = data[f"{filename}"]["right"]
        top = data[f"{filename}"]["top"]

        tif_path = os.path.join(predicted_chms_path, f'p{i}_{os.path.splitext(filename)[0]}.tif')
        
        height, width = y_pred_np.shape
        
        # writing the GeoTIFF file
        if not os.path.exists(tif_path):
            with rasterio.open(
                tif_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=y_pred_np.dtype,
                crs=utm,
                transform = rasterio.transform.from_bounds(left, bottom, right, top, width, height)
            ) as dst:
                dst.write(y_pred_np, 1)

if __name__ == '__main__':
 
    run_inference()


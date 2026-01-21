"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"""
A post-processing script performs pixelwise (loss = predicted-target) and treewise evaluation (identifies Tree Approximate Objects (TAOs) and calculates the RMSE and MAE based in meters). Written by Mia Mitchell in Atlanta, Georgia. Spring 2025.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import scipy.ndimage as ndi
import rasterio
import seaborn as sns
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from sklearn.metrics import mean_squared_error, mean_absolute_error
from dotenv import load_dotenv, find_dotenv

def treewise_pixelwise_evaluation():
    """
    Description
    ___________

    Main function for treewise and pixelwise evaluation
    """
    def read_chm(filepath, scale_factor=1):
        """
        Description
        ___________
        This function reads the GeoTIFF.

        Parameters
        __________
        filepath : str
            path to the GeoTIFF
        scale_factor : int
            Default is 1. This is for multiplying the heights of the canopy height model.

        Returns
        _______

        chm : array
            the GeoTIFF is read as an array
        
        """
        with rasterio.open(filepath) as src:
            chm = src.read(1) * scale_factor
            bounds = src.bounds
            resolution = chm.shape
        extent = {
            "left": bounds.left,
            "bottom": bounds.bottom,
            "right": bounds.right,
            "top": bounds.top
        }

        return chm
    def helper_segment_trees(target_canopy_height_model, predicted_canopy_height_model, min_tree_height=5):
        """
        Description
        ___________
        This helps segment trees by segmenting them with a local maximum and a watershed segmentation algorithm.

        Parameters
        __________
        target_canopy_height_model : arr
            the lidar-produced canopy height model array
        predicted_canopy_height_model : arr
            the MS-net predicated canopy height model array
        min_tree_height : int
            minimum tree height to search for the highest points

        Returns
        _______
        target_labels : arr
            the labels for the region from the target canopy height model
        predicted_labels : arr
            the labels for the region from the predicted canopy height model
        labels_for_plot : arr
            the labels for the plot
        local_maxi : arr
            the local maximum in the target canopy height model
        chm_mask : arr
            the mask where the height is greater than 5 meters
        
        """
        chm_array_smooth = ndi.gaussian_filter(target_canopy_height_model, 1, mode='constant',cval=0,truncate=2.0, radius = 10)
        chm_array_smooth[target_canopy_height_model < min_tree_height] = 0 # canopy height is less than 5m

        local_maxi = peak_local_max(chm_array_smooth,
                                footprint=np.ones((10, 10)), exclude_border=False,
                                labels=np.ones_like(chm_array_smooth, dtype=bool))
        
        local_maxi_mask = np.zeros_like(target_canopy_height_model, dtype=bool)
        local_maxi_mask[local_maxi[:, 0], local_maxi[:, 1]] = True
        
        # obtain 1s and 0s
        local_maxi_mask.astype(int)
        markers = ndi.label(local_maxi_mask)[0]
        
        # CHM mask so the segmentation will only occur on the trees
        chm_mask = chm_array_smooth
        chm_mask[chm_array_smooth != 0] = 1
        
        # perform watershed segmentation        
        target_labels = watershed(chm_array_smooth, markers, mask=chm_mask)
        predicted_labels = watershed(predicted_canopy_height_model, markers, mask=chm_mask) 
        labels_for_plot = np.array(target_labels,dtype = np.float32)
        labels_for_plot[labels_for_plot==0] = np.nan

        
        return target_labels, labels_for_plot, local_maxi, chm_mask
    def pearson_correlation(target, predicted, local_maxi):
        """
        Description
        ___________
        This function takes the locations of the local maximum in each region (from the watershed segmentation algorithm) from the target CHM and compares those values with the target's local maximum locations but from the predicted CHMs values. They are compared to find the mean absolute error and root mean square error.


        Parameters
        __________
        target : arr
            the target, lidar-produced CHM
        predicted : arr
            the predicted, CHMer produced CHM
        local_maxi : arr
            the locations of the local maximum in 


        Returns
        _______
        mae : float
            mean absolute error
        rmse : float
            root mean squared error
        target_highest_vals : arr
            the array of the highest values of the target CHM
        predicted_highest_vals : arr
            the array of the highest values of the predicted CHM


        """
        predicted_highest_vals = []
        predicted_highest_coords = []

        target_highest_vals = []
        target_highest_coords = []

        for i in range(len(local_maxi)):
            x, y = local_maxi[i]
            target_value = target[x, y]
            target_highest_vals.append(target_value)
            target_highest_coords.append(local_maxi[i])

            x, y = local_maxi[i]
            predicted_value = predicted[x, y]
            predicted_highest_vals.append(predicted_value)
            predicted_highest_coords.append(local_maxi[i])



        # metrics
        mse = mean_squared_error(target_highest_vals, predicted_highest_vals)
        mae = mean_absolute_error(target_highest_vals, predicted_highest_vals)
        rmse = np.sqrt(mse)

            
        return rmse, mae, target_highest_vals, predicted_highest_vals
    # Reading from the .env file
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    directory = os.getenv('project_path')
    predicted_tif_files = [file for file in os.listdir(os.path.join(directory, "outputs", "predicted_chms")) if file.endswith(".tif")]

    for tif in predicted_tif_files:
        predicted_tif_path = os.path.join(directory, "outputs", "predicted_chms", tif)
        target_tif_path = os.path.join(directory, "inputs", "chm", tif.split("_", 1)[1])
        input_tif_path = os.path.join(directory, "inputs", "wvimg", tif.split("_", 1)[1])

        # reading CHMs
        predicted = read_chm(predicted_tif_path)
        target = read_chm(target_tif_path)
        input = read_chm(input_tif_path)
       
        # performing the watershed segmentation
        target_labels, labels_for_plot, local_maxi, chm_mask= helper_segment_trees(target_canopy_height_model=target, predicted_canopy_height_model=predicted, min_tree_height=5)
        rmse, mae, target_highest_vals, predicted_highest_vals = pearson_correlation(target=target, predicted=predicted, local_maxi=local_maxi)

        #### Pixelwise Evaluation: Input, Target, Predicted, Loss Graph ####
        fig, axes = plt.subplots(1, 4, figsize=(20, 5))
        ax1, ax2, ax3, ax4 = axes

        vmin = 0
        vmax = max(predicted.max(), target.max())

        # Input
        im1 = ax1.imshow(input, cmap='gray')
        ax1.set_title('Input', fontsize=20)
        ax1.tick_params(labelsize=16)
        ax1.text(
            0.5, 0.5,
            f'file = {tif[3:]} ',
            transform=ax1.transAxes,
            fontsize=10,
            verticalalignment='bottom',
            horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
        )
        # Target CHM
        im2 = ax2.imshow(target, cmap='magma', vmin=vmin, vmax=vmax)
        ax2.set_title('Target CHM', fontsize=20)
        ax2.tick_params(labelsize=16)
        cbar2 = fig.colorbar(im2, ax=ax2, orientation='vertical', label='Height (m)')
        cbar2.ax.tick_params(labelsize=16)
        cbar2.set_label('Height (m)', fontsize=16)

        # Predicted CHM
        im3 = ax3.imshow(predicted, cmap='magma', vmin=vmin, vmax=vmax)
        ax3.set_title('Predicted CHM', fontsize=20)
        ax3.tick_params(labelsize=16)
        cbar3 = fig.colorbar(im3, ax=ax3, orientation='vertical', label='Height (m)')
        cbar3.ax.tick_params(labelsize=16)
        cbar3.set_label('Height (m)', fontsize=16)

        # Predicted CHM
        im4 = ax4.imshow(predicted-target, cmap='bwr')
        ax4.set_title('Prediction - Target', fontsize=20)
        ax4.tick_params(labelsize=16)
        cbar4 = fig.colorbar(im4, ax=ax4, orientation='vertical', label='Height (m)')
        cbar4.ax.tick_params(labelsize=16)
        cbar4.set_label('Differences in Height (m)', fontsize=16)

        output_directory = os.path.join(directory, "outputs", "pixelwise_charts")
        os.makedirs(output_directory, exist_ok=True)
        plt.tight_layout()  
        fig.savefig(os.path.join(output_directory, tif.split("_", 1)[1] + ".png"), dpi=300)
     
        #### Treewise Evaluation Loss Graph: MAE & RSME ####
        fig2, axes2 = plt.subplots(1, 3, figsize=(20, 5))
        ax1, ax2, ax4 = axes2

        # Target CHM
        im1 = ax1.imshow(target, cmap='magma', vmin=vmin, vmax=vmax)
        ax1.set_title('Target CHM', fontsize=20, pad=20)
        ax1.tick_params(labelsize=16)
        cbar1 = fig2.colorbar(im1, ax=ax1, orientation='vertical', label='Height (m)')
        cbar1.ax.tick_params(labelsize=16)
        cbar1.set_label('Height (m)', fontsize=16)

        # Predicted CHM
        im2 = ax2.imshow(predicted, cmap='magma', vmin=vmin, vmax=vmax)
        ax2.set_title('Predicted CHM', fontsize=20, pad=20)
        ax2.tick_params(labelsize=16)
        cbar2 = fig2.colorbar(im2, ax=ax2, orientation='vertical', label='Height (m)')
        cbar2.ax.tick_params(labelsize=16)
        cbar2.set_label('Height (m)', fontsize=16)

    # 2D histogram
        im4 = sns.histplot(
            x=predicted_highest_vals,
            y=target_highest_vals,
            bins=50,
            pmax=0.7,
            cmap="Blues",
            cbar=False,
            ax=ax4
        )
 
        # 1:1 reference line
        ax4.plot(
            [min(vmin), max(vmax)],
            [min(vmin), max(vmax)],
            color='black',
            linestyle='--',
            linewidth=1.5,
            label='1:1 Line'
        )
 

        ax4.set_title('Prediction versus Target', fontsize=20, pad=10)
        ax4.set_xlabel('Predicted Height (m)', fontsize=16)
        ax4.set_ylabel('Target Height (m)', fontsize=16)
        ax4.set_aspect('equal')
        ax4.legend()
        ax4.tick_params(labelsize=16)
 
        # Regression metrics text box
        ax4.text(
            0.95, 0.05,
            f'MAE = {mae:.2f} m\nRSME = {rmse:.2f}',
            transform=ax4.transAxes,
            fontsize=10,
            verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
        )
 

        output_directory_treewise = os.path.join(directory, "outputs", "treewise_charts")
        os.makedirs(output_directory_treewise, exist_ok=True)
        plt.tight_layout()  
        fig2.savefig(os.path.join(output_directory_treewise, tif.split("_", 1)[1] + ".png"), dpi=300)
        


    print(f"Finished creating pixelwise and treewise charts...saved in {output_directory_treewise}")
if __name__ == "__main__":
    treewise_pixelwise_evaluation()
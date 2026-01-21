"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""


"""
This script contains utility functions for 2D tensors.
"""
import numpy as np
import torch
import torch.nn as nn


def calc_loss(y_pred, y, loss_f, logs):
    """
    Description
    ___________
    This function calculates the loss between the output and ground truth labels (target). It updates the log dictionary with loss values at each scale and overall loss.

    Parameters
    __________
    y_pred : list of tensors
        model predictions at a different scale
    y : list of tensors
        the target tensors (ground truths)
    loss_f : function
        loss function to be used
    logs : dict
        dictionary to store loss

    Returns
    _______
    loss : list of tensors
        overall loss
    logs : dict
        updated dictionary
    """
    loss = 0
    y_var = y[-1].var()
    
    for scale, [y_hat,yi] in enumerate(zip(y_pred, y)):
        loss_scale = loss_f(y_hat,yi)/y_var 
        loss += loss_scale
                
        logs.setdefault(f'loss_scale_{scale}',0)
        logs[f'loss_scale_{scale}'] += loss_scale.item()
    logs.setdefault('loss',0)
    logs['loss'] += loss.item()
    
    return loss, logs




def mean_vel(y_pred):
    """
    Description
    ___________
    This calculates the mean of the predictions each scale.

    Parameters
    __________
    y_pred : list of tensors
        model predictions at a different scale

    Returns
    _______
    means : list
        list of means values 
    
    """
    means = []
    for pred in y_pred:
        means.append(pred.mean().item())
    return means




def scale_tensor(x, scale_factor=1, mode='nearest'):
    """
    Description
    ___________
    This scales the 2D tensor up or down using nearest neighbor interpolation. 

    Parameters
    __________
    x : tensor
        tensor to be scaled
    scale_factor : int
        factor that tensor should be scaled at
    Returns
    _______
    x : tensor
        the scaled tensor
    
    """
    
    if mode == 'nearest':
        if scale_factor<1:
            return nn.AvgPool2d(kernel_size = int(1/scale_factor))(x)
        
        elif scale_factor>1:
            for repeat in range (0, int(np.log2(scale_factor)) ):  #number of repeatsx2
                for ax in range(2,4):
                    x=x.repeat_interleave(repeats=2, axis=ax)
            return x
        
        elif scale_factor==1:
            return x
        
        else: raise ValueError(f"Scale factor not understood: {scale_factor}")
        
    else:
        NotImplemented

def get_masks(x, scales):
    """

    Description
    ___________
    This generates a set of masks (spatial information at a different scale) for the tensor 

    Parameters
    __________
    x : tensor
        the tensor that represents the euclidean distance at the finest scale
    scales : int
        the number of scales to generate masks for

    Returns
    _______
    masks[::-1] : list of tensors
        list of tensors represents a mask at a different scale
    
    
    x: euclidean distance 2d array at the finest scale
    Returns array with masks
    
    Notes:
        for n scales we need n masks (the last one is binary)
    """    
    masks    = [None]*(scales)
    pooled   = [None]*(scales)
    
    pooled[0] = (x>-1).float() # 0s at the solids, 1s at the empty space
    masks[0]  = pooled[0].squeeze(0)
    
    for scale in range(1,scales):
        pooled[scale] = nn.AvgPool2d(kernel_size = 2)(pooled[scale-1])
        denom = pooled[scale].clone()   # calculate the denominator for the mask
        denom[denom==0] = 1e8  # regularize to avoid divide by zero
        for ax in range(2,4):   # repeat along 3 axis
            denom=denom.repeat_interleave( repeats=2, axis=ax )
        masks[ scale ] = torch.div( pooled[scale-1], denom ).squeeze(0)
    return masks[::-1] # returns a list with masks. smallest size first
        
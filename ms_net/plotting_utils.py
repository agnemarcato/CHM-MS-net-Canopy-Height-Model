import numpy as np
import torch
import matplotlib
import h5py
from hdf5storage import loadmat
import matplotlib.pyplot as plt


params = {
    #'text.latex.preamble': '\\usepackage{gensymb}',
    'image.origin': 'lower',
    'image.interpolation': 'nearest',
    'image.cmap': 'inferno',
    'axes.grid': False,
    'savefig.dpi': 300,  # to adjust notebook inline plot size
    'figure.dpi': 300,
    'axes.labelsize': 8, # fontsize for x and y labels (was 10)
    'axes.titlesize': 8,
    'font.size': 8, # was 10
    'legend.fontsize': 6, # was 10
    'xtick.labelsize': 4,
    'ytick.labelsize': 4,
    #'text.usetex': True,
    'figure.figsize': [3.39, 2.10],
    'font.family': 'serif',
}
matplotlib.rcParams.update(params)




def colorbar(mappable):
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    last_axes = plt.gca()
    ax = mappable.axes
    fig = ax.figure
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = fig.colorbar(mappable, cax=cax)
    plt.sca(last_axes)
    return cbar




def plot_cs(y,yhat,error='L1',title=None,save_as=None):
    
    axis = -1
    mid  = y.shape[-1]//2
    
    y_cs  = y.cpu()
    yh_cs = yhat.cpu()
    
    if error == 'L1':
        e_cs = torch.abs(y_cs-yh_cs)
        e_cs[e_cs==0] = np.nan
        
        
    plt.subplot(1,3,1)
    im = plt.imshow(y_cs); 
    colorbar(im)
    plt.title('y')
    plt.subplot(1,3,2)
    im = plt.imshow(yh_cs, clim=(y_cs.min(), y_cs.max()));
    colorbar(im)
    plt.title('$\hat{y}$')
    plt.subplot(1,3,3)
    im = plt.imshow(e_cs, clim=(0, y_cs.max()));
    colorbar(im)
    plt.title(f'{error} error')
    
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(9, 3)
    #plt.show()
    
    if title:
        plt.suptitle(title)
    
    if save_as:    
        plt.savefig(save_as)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
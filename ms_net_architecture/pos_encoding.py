"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""

"""
This creates positional encoding in neural networks. 
"""
import numpy as np
import matplotlib.pyplot as plt


def positional_encoding(max_position, d_model, min_freq=1e-4):
    """
    Description
    ___________
    This function computes the positional encoding for a 2D input

    Parameters
    __________
    max_position :int
        the maximum position for which the positional encoding should be computed
    d_model : int
        the feature dimension (the embedding size) of the positional encoding
    min_freq : float, optional
        the minimum frequency used in the sinusoidal positional encoding. The default value is 1e-4

    Returns
    _______
    pos_enc : arry
        the minimum frequency used in the sinusoidal positional encoding
    """
    position = np.arange(max_position)
    freqs = min_freq ** (2 * (np.arange(d_model) // 2) / d_model)
    pos_enc = position.reshape(-1, 1) * freqs.reshape(1, -1)
    pos_enc[:, ::2] = np.cos(pos_enc[:, ::2])
    pos_enc[:, 1::2] = np.sin(pos_enc[:, 1::2])
    return pos_enc


def n_dim_pos_enc(max_position, d_model, dims, min_freq=1e-4):
    """
    Description
    ___________
    This function computes the positional encoding for an N-dimensional input, where the 1st dimension represents the position and the remaining dimensions represent the feature dimensions

    Parameters
    __________
    max_position : int
        the maximum position (e.g., the sequence length) for which the positional encoding should be computed.
    d_model : int
        the total feature dimension (also known as the embedding size) of the positional encoding.
    dims : list of ints
        a list of integers representing the dimensions of the positional encoding. The sum of the dimensions should be equal to d_model.
    min_freq : float
        the minimum frequency used in the sinusoidal positional encoding. The default value is 1e-4

    Returns
    _______
    os_enc : arry
        a multi-dimensional numpy array of shape (max_position, *dims) containing the positional encoding
    """
    if d_model % (len(dims) * 2) != 0:
        raise ValueError(
            "Cannot use sin/cos positional encoding with "
            "odd dimension (got dim={:d})".format(d_model)
        )

    d_model = 64 * 2
    dims = [10, 10]
    pos_enc_n = np.zeros((d_model, *dims))
    d_model = d_model // len(dims)

    pos_enc = []
    for i, dim_size in enumerate(dims):
        position = np.arange(dim_size)
        freqs = min_freq ** (2 * (np.arange(d_model) // 2) / d_model)
        pos_enc_1D = position.reshape(-1, 1) * freqs.reshape(1, -1)
        pos_enc_1D[:, ::2] = np.cos(pos_enc_1D[:, ::2])
        pos_enc_1D[:, 1::2] = np.sin(pos_enc_1D[:, 1::2])
        pos_enc.append(pos_enc_1D)

    for i, enc in enumerate(pos_enc):
        pos_enc_n[(d_model * 2) * i : (d_model * 2) * (i + 1) :, :] = np.repeat(
            pos_enc[i], dims[i], axis=0
        ).reshape(d_model * 2, *dims)
    # pos_enc = np.concatenate(pos_enc, axis=1)

### Plotting ####
d_model = 128
max_pos = 256
mat = positional_encoding(max_pos, d_model)
plt.pcolormesh(mat, cmap="copper")
plt.xlabel("Depth")
plt.xlim((0, d_model))
plt.ylabel("Position")
plt.title("PE matrix heat map")
plt.colorbar()
plt.show()

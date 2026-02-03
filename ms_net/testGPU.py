"""
© 2026. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
"""

# You should expect to see something like the below output, with your own GPU for the device name
# cuda available: True
# device count: 1
# current device idx: 0
# device name: NVIDIA RTX 3500 Ada Generation Laptop GPU
# memory allocated (bytes): 0
# memory reserved (bytes): 0

import torch
print("cuda available:", torch.cuda.is_available())
print("device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("current device idx:", torch.cuda.current_device())
    print("device name:", torch.cuda.get_device_name(0))
    print("memory allocated (bytes):", torch.cuda.memory_allocated(0))
    print("memory reserved (bytes):", torch.cuda.memory_reserved(0))


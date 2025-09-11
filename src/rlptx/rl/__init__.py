import torch
import torch.serialization
import numpy


# add these necessary numpy functionalities to the torch function allowlist used when loading 
# models with torch.load(..., weights_only=True); relevant in rlptx.rl.core.load_sac_agent
torch.serialization.add_safe_globals([
    numpy.core.multiarray._reconstruct, numpy.ndarray, numpy.dtype, 
    numpy.dtypes.Float32DType, numpy.dtypes.BoolDType
])


# make gpu accessible for network training in actor and critic if available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

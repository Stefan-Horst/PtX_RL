import torch

# use gpu for network training in actor and critic if available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

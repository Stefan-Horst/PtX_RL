import os
from pathlib import Path
import datetime
import yaml


PROJECT_FOLDER = "main"

def get_root_path(project_folder=PROJECT_FOLDER):
    current_path = Path().resolve()
    path = current_path
    for p in current_path.parents:
        if project_folder not in str(p):
            return path
        path = p
    return path

PROJECT_DIR = get_root_path()
DATA_DIR = PROJECT_DIR / "data"


def mkdir(path):
    os.makedirs(PROJECT_DIR / path, exist_ok=True)

def open_yaml_file(path):
    with open(path) as file:
        yaml_object = yaml.load(file, Loader=yaml.FullLoader)
    return yaml_object

def contains_only_unique_elements(list):
    return len(list) == len(set(list))

def get_timestamp():
    return str(datetime.datetime.now().replace(microsecond=0)).replace(':', '-').replace(' ', '_')

def set_seed(seed):
    """Set seed for all relevant modules."""
    import os
    import random
    import numpy as np
    import torch
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

import os
from pathlib import Path


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


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(get_root_path() / path)

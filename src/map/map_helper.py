
import os

from src.common.constants import RESOURCES_DIR


def get_maps_dir(name):
    return os.path.join(RESOURCES_DIR, 'maps', name)

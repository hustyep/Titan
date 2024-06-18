import numpy as np

from src.common.gui_setting import gui_setting
from src.common.constants import BotRunMode, MapPointType
from src.modules.capture import capture
from src.common import bot_status
from src.map.map_helper import *


def save_minimap_data(map_name: str, data):
    if gui_setting.mode.type != BotRunMode.Mapping:
        return
    try:
        minimap_data_file = f'{get_maps_dir(map_name)}.txt'
        np.savetxt(minimap_data_file, data,
                   fmt='%d', delimiter=",")
    except Exception as e:
        print(f'[!] save map: {minimap_data_file} failed! \n{e}')
    else:
        print(f" ~ Finished saving map data '{map_name}'")


def create_minimap_data(minimap_actual):
    if gui_setting.mode.type != BotRunMode.Mapping:
        return
    if minimap_actual is not None and len(minimap_actual) > 0:
        width = minimap_actual.shape[1] + 1
        height = minimap_actual.shape[0] + 1
        print(' ~ Created new minimap data \n')
        return np.zeros((height, width), np.uint8)
    else:
        print(' ! Create new minimap data failed \n')


def add_start_point(point: tuple[int, int], minimap_data):
    if gui_setting.mode.type != BotRunMode.Mapping:
        return
    print(f'\n[~] add start point {point}')

    x = point[0]
    y = point[1]
    line = minimap_data[y]
    line[x] = MapPointType.Floor.value

    for i in range(x - 1, -1, -1):
        if line[i] > 0:
            line[i] = 0
        else:
            break
    for i in range(x + 1, len(line)):
        if line[i] > 0:
            line[i] = 0
        else:
            break


def add_end_point(point: tuple[int, int], minimap_data):
    if gui_setting.mode.type != BotRunMode.Mapping:
        return
    print(f'\n[~] add end point {point}')

    x = point[0]
    y = point[1]
    line = minimap_data[y]
    line[x] = MapPointType.Floor.value

    for i in range(x - 1, -1, -1):
        if line[i] == 0:
            line[i] = 1
        else:
            break
    for i in range(x + 1, len(line)):
        if line[i] > 0:
            line[i] = 0
        else:
            break


def add_rope_point(point: tuple[int, int], minimap_data):
    if gui_setting.mode.type != BotRunMode.Mapping:
        return
    print(f'\n[~] add rope point {point}')
    
    x = point[0]
    y = point[1]
    minimap_data[y][x] = MapPointType.Rope.value
    for i in range(y - 1, -1, -1):
        if minimap_data[i][x] == 0:
            minimap_data[i][x] = 2
        elif minimap_data[i][x] == 1 or minimap_data[i][x] == 3:
            minimap_data[i][x] = 3
            break
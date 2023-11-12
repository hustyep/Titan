"""A module for saving map layouts and determining shortest paths."""

import os
import cv2
import math
import pickle
import xlrd
import numpy as np

from os.path import join, isfile, splitext, basename
from heapq import heappush, heappop
from src.common.constants import *
from src.modules.capture import capture


class MapPointType(Enum):
    Air = 0
    Floor = 1
    Rope = 2
    FloorRope = 3


class Map:
    """Uses a quadtree to represent possible player positions in a map layout."""

    def __init__(self):
        """
        Creates a new Layout object with the given NAME.
        :param name:     The name of this layout.
        """

        self.name = ''
        self.minimap_data = []
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []

    def clear(self):
        self.name = ''
        self.minimap_data = []
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []

    def load_data(self, map_name):
        self.clear()
        self.name = map_name
        self.load_minimap_data()
        self.load_mob_template()

    def load_minimap_data(self):
        resArray = []
        minimap_data_file = f'{get_maps_dir(self.name)}.xlsx'
        print(f"[~] Loading map '{minimap_data_file}'")
        try:
            data = xlrd.open_workbook(minimap_data_file)  # 读取文件
        except Exception as e:
            data = None
            print(f'[!] load map: {minimap_data_file}失败! \n{e}')
        if data:
            table = data.sheet_by_index(0)  # 按索引获取工作表，0就是工作表1
            for i in range(1, table.nrows):  # table.nrows表示总行数
                line = table.row_values(i)[1:]  # 读取每行数据，保存在line里面，line是list
                resArray.append(line)  # 将line加入到resArray中，resArray是二维list
            resArray = np.array(resArray)  # 将resArray从二维list变成数组
            self.minimap_data = resArray.astype(int)
        print(f" ~ Finished loading map '{self.name}'")

    def load_mob_template(self):
        try:
            mob_template = cv2.imread(f'assets/mobs/{self.name}_normal.png', 0)
            elite_template = cv2.imread(
                f'assets/mobs/{self.name}_elite.png', 0)
            boss_template = cv2.imread(f'assets/mobs/{self.name}_boss.png', 0)
        except:
            pass
        if mob_template is not None:
            self.mob_templates = [mob_template, cv2.flip(mob_template, 1)]

        if elite_template is not None:
            self.elite_templates = [
                elite_template, cv2.flip(elite_template, 1)]
        elif mob_template is not None:
            elite_template = cv2.resize(mob_template, None, fx=2, fy=2)
            self.elite_templates = [
                elite_template, cv2.flip(elite_template, 1)]

        if boss_template is not None:
            self.boss_templates = [boss_template, cv2.flip(boss_template, 1)]

    def point_type(self, point: tuple[int, int]):
        value = self.minimap_data[point[1]][point[0]]
        return MapPointType(value)

    def near_rope(self, location: tuple[int, int]):
        if self.minimap_data.any:
            height, width = self.minimap_data.shape
            cur_x = location[0]
            cur_y = location[1]
            start_x = max(0, cur_x - 3)
            end_x = min(width - 1, cur_x + 3)
            start_y = max(0, cur_y - 15)
            end_y = min(height - 1, cur_y + 5)
            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    if self.minimap_data[y][x] == 2:
                        return True
        return False

    def on_the_rope(self, location: tuple[int, int]):
        if self.minimap_data.any:
            point_type = self.point_type((location[0], location[1] + 7))
            if point_type == MapPointType.Floor or point_type == MapPointType.FloorRope:
                return False
            else:
                return self.point_type((location[0], location[1] + 3)) == MapPointType.Rope
        return False

    def on_the_platform(self, location: tuple[int, int]):
        x = location[0]
        y = location[1] + 7
        value = self.point_type((x, y))
        return value == MapPointType.Floor or value == MapPointType.FloorRope

    def platform_point(self, target: tuple[int, int]):
        if map.minimap_data.any:
            height, _ = map.minimap_data.shape
            for y in range(target[1] - 7, height - 1):
                p = (target[0], y)
                if map.on_the_platform(p):
                    return p

        return target

    def minimap_to_window(self, point: tuple[int, int]):
        '''convent the minimap point to the screen point'''
        window_width = capture.window['width']
        window_height = capture.window['height']

        mini_height, mini_width, _ = capture.minimap_actual.shape

        map_width = mini_width * MINIMAP_SCALE
        map_height = mini_height * MINIMAP_SCALE

        map_x = point[0] * MINIMAP_SCALE
        map_y = point[1] * MINIMAP_SCALE

        if map_x < window_width // 2:
            x = map_x
        elif map_width - map_x < window_width // 2:
            x = map_x - (map_width - window_width)
        else:
            x = window_width // 2

        if map_y < window_height // 2:
            y = map_y
        elif map_height - map_y < window_height // 2:
            y = map_y - (map_height - window_height)
        else:
            y = window_height // 2
        return (int(x), int(y))


def get_maps_dir(name):
    return os.path.join(RESOURCES_DIR, 'maps', name)


def run_if_map_available(function):
    """
    Decorator for functions that should only run if the bot is enabled.
    :param function:    The function to decorate.
    :return:            The decorated function.
    """

    def helper(*args, **kwargs):
        if map.minimap_data.any:
            return function(*args, **kwargs)
    return helper


map = Map()

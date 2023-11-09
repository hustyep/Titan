"""A module for saving map layouts and determining shortest paths."""

import os
import cv2
import math
import pickle
import xlrd
import numpy as np

from os.path import join, isfile, splitext, basename
from heapq import heappush, heappop
from src.common import constants


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
            self.minimap_data = resArray
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
        elif mob_template:
            elite_template = cv2.resize(mob_template, None, fx=2, fy=2)
            self.elite_templates = [
                elite_template, cv2.flip(elite_template, 1)]

        if boss_template is not None:
            self.boss_templates = [boss_template, cv2.flip(boss_template, 1)]

    def near_rope(location):
        if map.minimap_data:
            height, width = map.minimap_data.shape
            cur_x = location[0]
            cur_y = location[1]
            start_x = max(0, cur_x - 3)
            end_x = min(width - 1, cur_x + 3)
            start_y = max(0, cur_y - 15)
            end_y = min(height - 1, cur_y + 5)
            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    if map.minimap_data[x][y] == 2:
                        return True
        return False

    def on_the_rope(self, location:tuple[int, int]):
        if len(self.minimap_data) > 0:
            value = self.minimap_data[location[0]][location[1] + 7]
            if value == 1 or value == 3:
                return False
            else:
                return self.minimap_data[location[0]][location[1]] == 2
        return False

    def on_the_platform(self, location):
        x = location[0]
        y = location[1] - 7
        value: int = self.minimap_data[x][y]
        return value == 1 or value == 3

    def platform_point(target:tuple[int, int]):
        if map.minimap_data:
            height, _ = map.minimap_data.shape
            for y in range(target[1], height - 1):
                p = (target[0], y)
                if map.on_the_platform(p):
                    return p

        return target

def get_maps_dir(name):
    return os.path.join(constants.RESOURCES_DIR, 'maps', name)


map = Map()

"""A module for saving map layouts and determining shortest paths."""

import os
import cv2
import numpy as np

from os.path import join, isfile, splitext, basename
from src.common.constants import *
from src.modules.capture import capture
from src.common import bot_status

class MapPointType(Enum):
    Unknown = -1
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
        self.minimap_data = None
        self.minimap_sample = None
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []

    @property
    def data_available(self):
        return self.minimap_data is not None and len(self.minimap_data) > 0

    def clear(self):
        self.name = ''
        self.minimap_data = None
        self.minimap_sample = None
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []

    def load_data(self, map_name):
        self.clear()
        self.name = map_name
        self.load_minimap_data()
        self.load_mob_template()

    def load_minimap_data(self):
        map_dir = get_maps_dir(self.name)
        minimap_data_path = f'{map_dir}.txt'
        print(f"[~] Loading map '{minimap_data_path}'")
        if os.path.exists(minimap_data_path):
            try:
                self.minimap_data = np.loadtxt(
                    minimap_data_path, delimiter=',').astype(int)
            except Exception as e:
                print(f'[!] load map: {minimap_data_path} failed! \n{e}')
            else:
                print(f" ~ Finished loading map '{self.name}'")
        else:
            print(f" [!] map '{self.name}' not exist")

        minimap_sample_path = os.path.join(
            RESOURCES_DIR, 'maps', 'sample', f'{self.name}.png')
        if capture.minimap_display is not None:
            self.minimap_sample = capture.minimap_display
            cv2.imwrite(minimap_sample_path, capture.minimap_display)
        elif os.path.exists(minimap_sample_path):
            self.minimap_sample = cv2.imread(minimap_sample_path)

    def save_minimap_data(self):
        try:
            minimap_data_file = f'{get_maps_dir(self.name)}.txt'
            np.savetxt(minimap_data_file, self.minimap_data,
                       fmt='%d', delimiter=",")
        except Exception as e:
            print(f'[!] save map: {minimap_data_file} failed! \n{e}')
        else:
            print(f" ~ Finished saving map data '{self.name}'")

    def create_minimap_data(self):
        if capture.minimap_actual is not None and len(capture.minimap_actual) > 0:
            width = capture.minimap_actual.shape[1] + 1
            height = capture.minimap_actual.shape[0] + 1
            if self.minimap_data is not None:
                try:
                    m_height, m_widht = self.minimap_data.shape
                except Exception as e:
                    print(e)
                    self.minimap_data = np.zeros((height, width), np.uint8)
                    print(' ~ Created new minimap data \n')
                else:
                    if m_widht != width or m_height != height:
                        self.minimap_data = np.zeros((height, width), np.uint8)
                        print(' ~ Created new minimap data \n')
            else:
                self.minimap_data = np.zeros((height, width), np.uint8)
                print(' ~ Created new minimap data \n')
        else:
            print('[!] create minimap data failed! \n')

    @bot_status.run_if_disabled('')
    def add_start_point(self, point: tuple[int, int]):
        print(f'\n[~] add start point {point}')

        self.create_minimap_data()
        x = point[0]
        y = point[1]
        line = self.minimap_data[y]
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
        self.save_minimap_data()

    @bot_status.run_if_disabled('')
    def add_end_point(self, point: tuple[int, int]):
        print(f'\n[~] add end point {point}')
        self.create_minimap_data()
        x = point[0]
        y = point[1]
        line = self.minimap_data[y]
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
        self.save_minimap_data()

    @bot_status.run_if_disabled('')
    def add_rope_point(self, point: tuple[int, int]):
        print(f'\n[~] add rope point {point}')
        self.create_minimap_data()
        x = point[0]
        y = point[1]
        self.minimap_data[y][x] = MapPointType.Rope.value
        for i in range(y - 1, -1, -1):
            if self.minimap_data[i][x] == 0:
                self.minimap_data[i][x] = 2
            elif self.minimap_data[i][x] == 1 or self.minimap_data[i][x] == 3:
                self.minimap_data[i][x] = 3
                break
        self.save_minimap_data() 

    def load_mob_template(self):
        try:
            mob_template = cv2.imread(f'assets/mobs/{self.name}@normal.png', 0)
            elite_template = cv2.imread(
                f'assets/mobs/{self.name}@elite.png', 0)
            boss_template = cv2.imread(f'assets/mobs/{self.name}@boss.png', 0)
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
        height, width = self.minimap_data.shape
        if point[0] >= width or point[1] >= height:
            return MapPointType.Unknown

        if self.data_available:
            value = self.minimap_data[point[1]][point[0]]
            return MapPointType(value)
        else:
            return MapPointType.Unknown

    def near_rope(self, location: tuple[int, int]):
        if self.data_available:
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
        if self.data_available:
            point_type = self.point_type((location[0], location[1] + 7))
            if point_type == MapPointType.Floor or point_type == MapPointType.FloorRope:
                return False
            else:
                for i in range(1, 7):
                    if self.point_type((location[0], location[1] + i)) == MapPointType.Rope:
                        return True 
        return False

    def on_the_platform(self, location: tuple[int, int]):
        if self.data_available:
            x = location[0]
            y = location[1] + 7
            value = self.point_type((x, y))
            return value == MapPointType.Floor or value == MapPointType.FloorRope
        else:
            return True

    def platform_point(self, target: tuple[int, int]):
        if self.data_available:
            height, _ = shared_map.minimap_data.shape
            for y in range(target[1] - 7, height - 1):
                p = (target[0], y)
                if shared_map.on_the_platform(p):
                    return p

        return target

    def valid_point(self, p: tuple[int, int]):
        if self.data_available:
            height, width = self.minimap_data.shape
            x = min(max(0, p[0]), width - 1)
            y = min(max(0, p[1]), height - 1)
            return (x, y)
        return p

    def is_continuous(self, p1, p2, max_gap=0):
        if self.data_available:
            if p1[1] != p2[1]:
                return False
            if not self.on_the_platform(p1) or not self.on_the_platform(p2):
                return False
            gap = 0
            y = p1[1]
            for x in range(p1[0], p2[0]):
                if self.on_the_platform((x, y)):
                    gap = 0
                else:
                    gap += 1
                if gap > max_gap:
                    return False

            return True
        else:
            return True


def get_maps_dir(name):
    return os.path.join(RESOURCES_DIR, 'maps', name)


def run_if_map_available(function):
    """
    Decorator for functions that should only run if the bot is enabled.
    :param function:    The function to decorate.
    :return:            The decorated function.
    """

    def helper(*args, **kwargs):
        if shared_map.data_available:
            return function(*args, **kwargs)
    return helper


shared_map = Map()

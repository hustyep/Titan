from enum import Enum
import os
import cv2
import numpy as np
from typing import List
from collections import OrderedDict

from src.map import map_helper
from src.common.constants import RESOURCES_DIR, Platform, MapPointType
from src.modules.capture import capture


class MapType(Enum):
    Sacred = 'Sacred'
    Arcane = 'Arcane'
    Normal = 'Normal'


class MapModel:
    def __init__(self, dict):
        self.name = str(dict["MapName"])
        self.type = MapType(value=dict["Type"])
        self.zone = str(dict["Zone"])
        self.monster = str(dict["Monster"])
        self.mobs_count = int(dict["MobsCount"])
        self.minimap_margin = int(dict["MinimapMargin"])

        self.minimap_data = None
        self.minimap_sample = None
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []
        self.platforms = OrderedDict()

    @property
    def instance(self) -> bool:
        return self.type == MapType.Sacred
    
    @property
    def base_floor(self):
        if len(self.platforms) == 0:
            return 0
        return int(list(self.platforms.keys())[-1])

    def load_data(self):
        self._load_minimap_data()
        self._load_minimap_sample()
        self._load_mob_template()

    def clear(self):
        self.minimap_data = None
        self.minimap_sample = None
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []
        self.platforms.clear()

    def _load_minimap_data(self):
        map_dir = map_helper.get_maps_dir(self.name)
        minimap_data_path = f'{map_dir}.txt'
        print(f"[~] Loading map '{minimap_data_path}'")
        if os.path.exists(minimap_data_path):
            try:
                self.minimap_data = np.loadtxt(
                    minimap_data_path, delimiter=',').astype(int)
            except Exception as e:
                print(f'[!] load map: {minimap_data_path} failed! \n{e}')
            else:
                height, width = self.minimap_data.shape
                for y in range(0, height):
                    for x in range(0, width):
                        value = MapPointType(self.minimap_data[y][x])
                        if value != MapPointType.Floor and value != MapPointType.FloorRope:
                            continue
                        platform_list: List[Platform] | None = self.platforms.get(str(y))
                        if platform_list is None:
                            platform_list = [Platform(x, x, y)]
                            self.platforms[str(y)] = platform_list
                        else:
                            last_platform: Platform = platform_list[-1]
                            if last_platform.end_x == x - 1:
                                last_platform.end_x = x
                            else:
                                platform_list.append(Platform(x, x, y))

                print(f" ~ Finished loading map '{self.name}'")
        else:
            print(f" [!] map '{self.name}' not exist")

    def _load_minimap_sample(self):
        minimap_sample_path = os.path.join(
            RESOURCES_DIR, 'maps', 'sample', f'{self.name}.png')
        if os.path.exists(minimap_sample_path):
            self.minimap_sample = cv2.imread(minimap_sample_path)
        elif capture.minimap_display is not None:
            self.minimap_sample = capture.minimap_display
            cv2.imwrite(minimap_sample_path, capture.minimap_display)

    def _load_mob_template(self):
        mob_template = None
        elite_template = None
        boss_template = None
        try:
            mob_template = cv2.imread(
                f'assets/mobs/{self.monster}@normal.png', 0)
            elite_template = cv2.imread(
                f'assets/mobs/{self.monster}@elite.png', 0)
            # boss_template = cv2.imread(
            #     f'assets/mobs/{self.monster}@boss.png', 0)
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

        # if boss_template is not None:
        #     self.boss_templates = [boss_template, cv2.flip(boss_template, 1)]

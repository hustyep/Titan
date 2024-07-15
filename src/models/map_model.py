from enum import Enum
import os
import cv2
import numpy as np
from typing import List, Dict

from src.map import map_helper
from src.common.constants import RESOURCES_DIR, Platform, MapPointType, MapPoint, Portal, Path
from src.modules.capture import capture

Min_Jumpable_Gap = 5
Max_Jumpable_Gap = 26
Max_Path_Step = 5


class MapType(Enum):
    Sacred = 'Sacred'
    Arcane = 'Arcane'
    Normal = 'Normal'


class MapModel:
    def __init__(self, dict):
        self.name = str(dict["MapName"])
        self.type = MapType(value=dict["Type"])
        self.zone = str(dict["Zone"])
        self.monsters = str(dict["Monster"]).split(',')
        self.mobs_count = int(dict["MobsCount"])
        self.minimap_margin = int(dict["MinimapMargin"])
        self.portals = self.__load_portals(str(dict['Portals']))

        self.minimap_data = None
        self.minimap_sample = None
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []

        self.platforms: set[Platform] = set()
        self.platform_map: Dict[int, List[Platform]] = {}
        self.single_path: Dict[Platform, set[Platform]] = {}
        self.path_map: Dict[tuple[Platform, Platform], List[Path]] = {}

    @property
    def instance(self) -> bool:
        return self.type == MapType.Sacred

    @property
    def base_floor(self):
        if len(self.platforms) == 0:
            return 0
        y_list = list(self.platform_map.keys())
        y_list.sort()
        return y_list[-1]

    def load_data(self):
        self.load_minimap_data()
        self._load_minimap_sample()
        self._load_mob_template()

        self.init_path()

    def clear(self):
        self.minimap_data = None
        self.minimap_sample = None
        self.mob_templates = []
        self.elite_templates = []
        self.boss_templates = []
        self.platforms.clear()

    def load_minimap_data(self):
        map_dir = map_helper.get_maps_dir(self.name)
        minimap_data_path = f'{map_dir}.txt'
        print(f"[~] Loading map '{minimap_data_path}'")
        if not os.path.exists(minimap_data_path):
            print(f" [!] map '{self.name}' not exist")

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
                    platform_list: List[Platform] = []
                    if y in self.platform_map.keys():
                        platform_list = self.platform_map[y]
                    if not platform_list:
                        platform_list = [Platform(x, x, y)]
                        self.platform_map[y] = platform_list
                    else:
                        last_platform: Platform = platform_list[-1]
                        if last_platform.end_x == x - 1:
                            last_platform.end_x = x
                        else:
                            platform_list.append(Platform(x, x, y))

            print(f" ~ Finished loading map '{self.name}'")

    def __load_portals(self, config: str) -> list[Portal]:
        if not config:
            return []
        else:
            result = []
            portals_str_list = config.split(';')
            for portals_str in portals_str_list:
                points_str = portals_str.split(':')
                entrance_str = points_str[0].split(',')
                export_str = points_str[1].split(',')
                entrance = MapPoint(int(entrance_str[0]), int(entrance_str[1], 1))
                export = MapPoint(int(export_str[0]), int(export_str[1], 1))
                result.append(Portal(entrance, export))
            return result
                

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
        for monster in self.monsters:
            try:
                mob_template = cv2.imread(
                    f'assets/mobs/{monster}@normal.png', 0)
            except:
                pass
            if mob_template is not None:
                self.mob_templates.append(mob_template)
                self.mob_templates.append(cv2.flip(mob_template, 1))

    def init_path(self):
        for platforms in self.platform_map.values():
            self.platforms |= set(platforms)

        for plat1 in self.platforms:
            self.single_path[plat1] = set()
            for plat2 in self.platforms:
                if plat1 == plat2:
                    continue
                self.path_map[(plat1, plat2)] = []
                if self.platform_reachable(plat1, plat2):
                    self.single_path[plat1].add(plat2)
                    self.path_map[(plat1, plat2)].append(Path([plat1, plat2]))

        def weight_of_path(path: Path):
            return path.weight

        for plat1 in self.platforms:
            for plat2 in self.platforms:
                if plat1 == plat2:
                    continue
                if self.path_map[(plat1, plat2)]:
                    continue
                paths = self.path_between(plat1, plat2, Path([]))
                paths.sort(key=weight_of_path)
                self.path_map[(plat1, plat2)] = paths

    def platforms_of_y(self, y: int) -> List[Platform] | None:
        assert (self.platforms)
        if y in self.platform_map.keys():
            return self.platform_map[y]

    def adjoin_platform(self, platform: Platform, right=True):
        assert (platform)
        platforms = self.platforms_of_y(platform.y)
        assert (platforms)
        index = platforms.index(platform)
        if right:
            if index + 1 < len(platforms):
                return platforms[index + 1]
        else:
            if index - 1 >= 0:
                return platforms[index - 1]

    def platform_reachable(self, platform_start: Platform | None, platform_target: Platform | None):
        if platform_start is None or platform_target is None:
            return False
        dy = platform_target.y - platform_start.y
        gap = map_helper.platform_gap(platform_start, platform_target)

        if dy == 0:
            return gap <= Max_Jumpable_Gap
        elif dy < 0:
            if gap <= -Min_Jumpable_Gap:
                return True
            return gap <= 8 and abs(dy) <= 8
        else:
            if gap <= -Min_Jumpable_Gap:
                return True
            if gap <= 26:
                for y in range(platform_start.y, platform_target.y):
                    plats = self.platforms_of_y(y)
                    if plats:
                        for plat in plats:
                            start_x = max(platform_target.begin_x, platform_target.end_x - 30)
                            xs_target = list(range(start_x, platform_target.end_x+1))
                            xs_pat = list(range(plat.begin_x, plat.end_x+1))
                            intersections = set(xs_target).intersection(set(xs_pat))
                            if intersections:
                                return False
                return True
            return False

    def path_between(self, platform_start: Platform, platform_target: Platform, path: Path = Path([])) -> list[Path]:
        if path.steps >= Max_Path_Step:
            return []

        if platform_start in path.routes or platform_target in path.routes:
            return []

        paths = self.path_map[(platform_start, platform_target)]
        if paths:
            result = []
            for tmp in paths:
                if path.steps + tmp.steps <= Max_Path_Step:
                    result.append(tmp)
            return result

        new_path = Path(path.routes + [platform_start])
        dy = platform_target.y - platform_start.y
        reachable_plats = self.single_path[platform_start]
        result: List[Path] = []
        for plat in reachable_plats:
            if plat in path.routes:
                continue
            if dy == 0:
                if plat.y != platform_start.y:
                    continue
                dx = platform_target.begin_x - platform_start.begin_x
                if dx > 0 and plat.begin_x < platform_start.begin_x:
                    continue
                elif dx < 0 and plat.begin_x > platform_start.begin_x:
                    continue
            elif dy < 0:
                if plat.y > platform_start.y:
                    continue
            else:
                if plat.y < platform_start.y:
                    continue
            next_paths = self.path_between(plat, platform_target, new_path)
            if next_paths:
                for sub_path in next_paths:
                    if new_path.steps + sub_path.steps <= Max_Path_Step:
                        next_path = [platform_start] + sub_path.routes
                        result.append(Path(next_path))

        return result

    def upper_platform(self, platform: Platform):
            assert (platform)
            for y in range(platform.y - 1, 0, -1):
                platforms = self.platforms_of_y(y)
                if platforms is not None:
                    for tmp in platforms:
                        if map_helper.platform_gap(platform, tmp) <= -3:
                            return tmp

    def under_platform(self, platform: Platform):
        assert (platform)
        for y in range(platform.y + 1, self.base_floor + 1):
            platforms = self.platforms_of_y(y)
            if platforms is not None:
                for tmp in platforms:
                    if map_helper.platform_gap(platform, tmp) <= -3:
                        return tmp
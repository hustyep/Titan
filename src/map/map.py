"""A module for saving map layouts and determining shortest paths."""

from typing import List

from src.common.constants import *
from src.common import utils
from src.common.gui_setting import gui_setting
from src.map import map_editor, map_helper
from src.models.map_model import MapModel
from src.modules.capture import capture


class Map:
    """Map Manager."""

    def __init__(self):
        self.current_map: MapModel | None = None
        self.available_maps: List[MapModel] = []
        self._load_data()

    def _load_data(self):
        file_path = f"{RESOURCES_DIR}/maps/maplestory_maps.xlsx"
        map_list = utils.load_excel(file_path)
        available_maps = []
        for map in map_list:
            available_maps.append(MapModel(map))
        self.available_maps = available_maps

    @property
    def current_map_name(self):
        if self.current_map != None:
            return self.current_map.name

    @property
    def minimap_data(self):
        if self.current_map != None:
            return self.current_map.minimap_data

    @property
    def data_available(self):
        return self.minimap_data is not None and len(self.minimap_data) > 0

    def clear(self):
        if self.current_map is not None:
            self.current_map.clear()
            self.current_map = None
            capture.minimap_margin = 0

    def load_map(self, map_name: str):
        self.clear()
        for map in self.available_maps:
            if map.name == map_name:
                map.load_data()
                self.current_map = map
                capture.minimap_margin = map.minimap_margin
                break

    def point_type(self, point: MapPoint):
        if self.data_available:
            height, width = self.minimap_data.shape  # type: ignore
            if point.x >= width or point.y >= height:
                return MapPointType.Unknown
            value = self.minimap_data[point.y][point.x]  # type: ignore
            return MapPointType(value)
        else:
            return MapPointType.Unknown

    def near_rope(self, location: MapPoint, up=False):
        if self.data_available:
            cur_x = location.x
            cur_y = location.y
            if up:
                for x in range(cur_x - 1, cur_x + 2):
                    for y in range(cur_y, cur_y - 7, -1):
                        if self.point_type(MapPoint(x, y)) == MapPointType.Rope:
                            return True
            else:
                for x in range(cur_x - 1, cur_x + 2):
                    if self.point_type(MapPoint(x, cur_y)) == MapPointType.FloorRope:
                        return True
        return False

    def on_the_rope(self, location: MapPoint):
        if self.data_available:
            point_type = self.point_type(location)
            if point_type == MapPointType.Floor or point_type == MapPointType.FloorRope:
                return False
            else:
                for i in range(-2, 3):
                    if self.point_type(MapPoint(location.x, location.y + i)) == MapPointType.Rope:
                        utils.log_event("检测到在绳子上")
                        return True
        return False

    def on_the_platform(self, location: MapPoint, range=0):
        if self.data_available:
            x = location.x
            y = location.y
            value = self.is_floor_point(location)
            if range == 0:
                return value
            else:
                if value:
                    p_l = MapPoint(x - range, y)
                    p_r = MapPoint(x + range, y)
                    return self.is_continuous(p_l, p_r)
                return False
        else:
            return True

    def platform_point(self, target: MapPoint):
        if self.data_available:
            height, _ = self.minimap_data.shape  # type: ignore
            for y in range(target.y, height - 1):
                p = MapPoint(target.x, y, target.tolerance)
                if shared_map.on_the_platform(p):
                    return p

        return target

    def fixed_point(self, p: MapPoint):
        if self.data_available:
            fixed_p = shared_map.platform_point(p)
            # y值稍微偏离情况
            if abs(fixed_p.y - p.y) <= p.tolerance_v:
                return fixed_p
        return p

    def valid_point(self, p: MapPoint):
        if self.data_available:
            height, width = self.minimap_data.shape  # type: ignore
            x = min(max(0, p.x), width - 1)
            y = min(max(0, p.y), height - 1)
            return MapPoint(x, y, p.tolerance)
        return p

    def is_floor_point(self, point: MapPoint, count_none=False):
        value = self.point_type(point)
        if count_none:
            return value == MapPointType.Unknown or value == MapPointType.Floor or value == MapPointType.FloorRope
        else:
            return value == MapPointType.Floor or value == MapPointType.FloorRope

    def is_continuous(self, p1: MapPoint, p2: MapPoint):
        if self.data_available:
            if p1.y != p2.y:
                return False
            if not self.on_the_platform(p1) or not self.on_the_platform(p2):
                return False
            y = p1.y
            for x in range(p1.x, p2.x, 1 if p2.x > p1.x else -1):
                if not self.on_the_platform(MapPoint(x, y)):
                    return False
            return True
        else:
            return True

    def on_the_edge(self, p: MapPoint, tolerance=5):
        platform = self.platform_of_point(p)
        if not platform:
            return False
        return abs(p.x - platform.begin_x) <= tolerance or abs(p.x - platform.end_x) <= tolerance

    def point_direction_on_platform(self, p: MapPoint):
        platform = self.platform_of_point(p)
        assert (platform)
        return 'left' if abs(p.x - platform.begin_x) <= abs(p.x - platform.end_x) else 'right'

    def platform_of_point(self, p: MapPoint) -> Platform | None:
        if not self.data_available:
            return
        if not self.is_floor_point(p):
            return
        else:
            platform_list: List[Platform] = self.current_map.platforms[str(p.y)]  # type: ignore
            for platform in platform_list:
                if p.x in range(platform.begin_x, platform.end_x+1):
                    return platform

    def point_of_intersection(self, platform_start: Platform, platform_target: Platform):
        x_start = list(range(platform_start.begin_x, platform_start.end_x + 1))
        x_target = list(range(platform_target.begin_x, platform_target.end_x + 1))
        x_intersection = list(set(x_start).intersection(set(x_target)))
        if len(x_intersection) > 0:
            x_intersection.sort()
            target_x = (x_intersection[0] + x_intersection[-1]) / 2
            return MapPoint(int(target_x), platform_start.y, 2)

    def platforms_of_y(self, y: int) -> List[Platform] | None:
        assert (self.current_map)
        if str(y) in self.current_map.platforms.keys():
            return self.current_map.platforms[str(y)]

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

    def upper_platform(self, platform: Platform):
        assert (platform)
        for y in range(platform.y - 1, 0, -1):
            platforms = self.platforms_of_y(y)
            if platforms is not None:
                for tmp in platforms:
                    if map_helper.platform_gap(platform, tmp) == -1:
                        return tmp

    def under_platform(self, platform: Platform):
        assert (platform)
        assert (self.current_map)
        for y in range(platform.y + 1, self.current_map.base_floor + 1):
            platforms = self.platforms_of_y(y)
            if platforms is not None:
                for tmp in platforms:
                    if map_helper.platform_gap(platform, tmp) == -1:
                        return tmp

    def gap_of_points_platform(self, p1: MapPoint, p2: MapPoint):
        if self.is_continuous(p1, p2):
            return 0
        platform1 = self.platform_of_point(p1)
        platform2 = self.platform_of_point(p2)
        return map_helper.platform_gap(platform1, platform2)

    def point_reachable(self, start: MapPoint, target: MapPoint):
        assert (self.on_the_platform(target))
        dx = target.x - start.x
        dy = target.y - start.y
        platform_start = self.platform_of_point(start)
        platform_target = self.platform_of_point(target)

        if abs(dx) <= target.tolerance and abs(dy) <= target.tolerance_v:
            return True
        if abs(dx) <= 1:
            return True
        if platform_start is None or platform_target is None:
            return False
        return self.platform_reachable(platform_start, platform_target)

    def platform_reachable(self, platform_start: Platform | None, platform_target: Platform | None):
        if platform_start is None or platform_target is None:
            return False
        dy = platform_target.y - platform_start.y
        gap = map_helper.platform_gap(platform_start, platform_target)

        if dy == 0:
            return gap <= 26
        elif dy < 0:
            if gap == -1:
                return True
            return gap <= 8 and abs(dy) <= 8
        else:
            if gap == -1:
                return True
            return gap <= 26

    def path_between(self, platform_start: Platform | None, platform_target: Platform | None) -> list[Platform] | None:
        if platform_start is None or platform_target is None:
            return None
        dy = platform_target.y - platform_start.y

        if platform_start == platform_target:
            return [platform_start]
        if self.platform_reachable(platform_start, platform_target):
            return [platform_start, platform_target]

        if dy == 0:
            next_platform = self.adjoin_platform(platform_start, platform_target.begin_x > platform_start.end_x)
            if self.platform_reachable(platform_start, next_platform):
                paths = self.path_between(next_platform, platform_target)
                if paths:
                    return [platform_start] + paths
        else:
            if platform_target.begin_x > platform_start.end_x:
                adjoin_platform = self.adjoin_platform(platform_start, True)
                if adjoin_platform and self.platform_reachable(platform_start, adjoin_platform) and adjoin_platform.begin_x < platform_target.end_x:
                    paths = self.path_between(adjoin_platform, platform_target)
                    if paths:
                        return [platform_start] + paths
            else:
                adjoin_platform = self.adjoin_platform(platform_start, False)
                if adjoin_platform and self.platform_reachable(platform_start, adjoin_platform) and adjoin_platform.end_x > platform_target.begin_x:
                    paths = self.path_between(adjoin_platform, platform_target)
                    if paths:
                        return [platform_start] + paths

            if dy < 0:
                upper_platform = self.upper_platform(platform_start)
                if upper_platform and upper_platform.y <= platform_target.y:
                    paths = self.path_between(upper_platform, platform_target)
                    if paths:
                        return [platform_start] + paths
            else:
                under_platform = self.under_platform(platform_start)
                paths = self.path_between(under_platform, platform_target)
                if paths:
                    return [platform_start] + paths

    def add_start_point(self, point: MapPoint):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            self.current_map.minimap_data = map_editor.create_minimap_data(  # type: ignore
                capture.minimap_frame)
        if not self.data_available:
            return
        map_editor.add_start_point(point, self.minimap_data)
        if self.current_map is not None:
            map_editor.save_minimap_data(self.current_map.name, self.minimap_data)

    def add_end_point(self, point: MapPoint):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            return
        map_editor.add_end_point(point, self.minimap_data)
        map_editor.save_minimap_data(self.current_map.name, self.minimap_data)  # type: ignore

    def add_rope_point(self, point: MapPoint):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            return
        map_editor.add_rope_point(point, self.minimap_data)
        map_editor.save_minimap_data(self.current_map.name, self.minimap_data)  # type: ignore


shared_map = Map()

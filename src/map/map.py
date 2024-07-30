"""A module for saving map layouts and determining shortest paths."""

from typing import List
import random

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
                for x in range(cur_x - 2, cur_x + 3):
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
        if not self.current_map:
            return
        return self.current_map.platform_of_point(p)

    def point_portable(self, start: MapPoint, target: MapPoint):
        if not self.current_map:
            return
        return self.current_map.point_portable(start, target)

    def path_between(self, start: MapPoint, target: MapPoint, random_path=False) -> list[Platform]:
        platform_start = self.platform_of_point(start)
        platform_target = self.platform_of_point(target)
        assert platform_start
        assert platform_target
        assert self.current_map
        paths = self.current_map.path_between(platform_start, platform_target)
        if paths:
            paths.sort(key=lambda path: self.weight_of_full_path(path, start, target))
            if random_path:
                paths = paths[:3]
                index = random.randrange(0, len(paths))
                return paths[index].routes
            else:
                return paths[0].routes
        return []
    
    def weight_of_full_path(self, path: Path, start: MapPoint, target: MapPoint):
        assert self.current_map
        if path.steps <= 1:
            return sys.maxsize

        last = start
        points = self.current_map.points_of_path(path, start, target)
        result = len(points) * 3
        for point in points:
            if point == start:
                continue
            result += abs(point.y - last.y)
            result += abs(point.x - last.x)
            last = point
        return result

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

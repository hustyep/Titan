"""A module for saving map layouts and determining shortest paths."""

from src.common.constants import *
from src.common import utils
from src.common.gui_setting import gui_setting
from src.map import map_editor
from src.models.map_model import MapModel
from src.modules.capture import capture


class Map:
    """Map Manager."""

    def __init__(self):
        self.current_map: MapModel = None
        self.available_maps = [MapModel]
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

    def load_map(self, map_name):
        self.clear()
        for map in self.available_maps:
            if map.name == map_name:
                map.load_data()
                self.current_map = map
                capture.minimap_margin = map.minimap_margin
                break

    def point_type(self, point: tuple[int, int]):
        if self.data_available:
            height, width = self.minimap_data.shape
            if point[0] >= width or point[1] >= height:
                return MapPointType.Unknown
            value = self.minimap_data[point[1]][point[0]]
            return MapPointType(value)
        else:
            return MapPointType.Unknown

    def near_rope(self, location: tuple[int, int], up=False):
        if self.data_available:
            cur_x = location[0]
            cur_y = location[1]
            if up:
                for x in range(cur_x - 1, cur_x + 2):
                    for y in range(cur_y, cur_y - 7, -1):
                        if self.point_type((x, y)) == MapPointType.Rope:
                            return True
            else:
                for x in range(cur_x - 1, cur_x + 2):
                    if self.point_type((x, cur_y)) == MapPointType.FloorRope:
                        return True
        return False

    def on_the_rope(self, location: tuple[int, int]):
        if self.data_available:
            point_type = self.point_type(location)
            if point_type == MapPointType.Floor or point_type == MapPointType.FloorRope:
                return False
            else:
                for i in range(-2, 3):
                    if self.point_type((location[0], location[1] + i)) == MapPointType.Rope:
                        return True
        return False

    def on_the_platform(self, location: tuple[int, int], strict=False):
        if self.data_available:
            x = location[0]
            y = location[1]
            value = self.is_floor_point(location)
            if not strict:
                return value
            else:
                if value:
                    value_l = self.is_floor_point((x - 1, y))
                    value_r = self.is_floor_point((x + 1, y))
                    return value_l and value_r
                return False
        else:
            return True

    def platform_point(self, target: tuple[int, int]):
        if self.data_available:
            height, _ = self.minimap_data.shape
            for y in range(target[1], height - 1):
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

    def is_floor_point(self, point):
        value = self.point_type(point)
        return value == MapPointType.Unknown or value == MapPointType.Floor or value == MapPointType.FloorRope

    def is_continuous(self, p1, p2):
        if self.data_available:
            if p1[1] != p2[1]:
                return False
            if not self.on_the_platform(p1) or not self.on_the_platform(p2):
                return False
            y = p1[1]
            for x in range(p1[0] + 1, p2[0], 1 if p2[0] > p1[0] else -1):
                if not self.on_the_platform((x, y)):
                    return False
            return True
        else:
            return True

    def boundary_point(self, point):
        left = right = point[0]
        left_boundary = right_boundary = None
        while True:
            if left > 0 and self.point_type((left - 1, point[1])) != MapPointType.Air:
                left -= 1
            else:
                left_boundary = (left, point[1])
                break
        while True:
            next_point = (right + 1, point[1])
            if self.point_type(next_point) != MapPointType.Air and self.point_type(next_point) != MapPointType.Unknown:
                right += 1
            else:
                right_boundary = (right, point[1])
                break

        return left_boundary, right_boundary

    def horizontal_gap(self, p1, p2):
        if self.is_continuous(p1, p2):
            return 0
        left_boundary1, right_boundary1 = self.boundary_point(p1)
        left_boundary2, right_boundary2 = self.boundary_point(p2)
        if right_boundary1[0] < left_boundary2[0]:
            return left_boundary2[0] - right_boundary1[0]
        elif right_boundary2[0] < left_boundary1[0]:
            return left_boundary1[0] - right_boundary2[0]
        else:
            return -1

    def add_start_point(self, point: tuple[int, int]):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            self.current_map.minimap_data = map_editor.create_minimap_data(
                capture.minimap_frame)
        if not self.data_available:
            return
        map_editor.add_start_point(point, self.minimap_data)
        map_editor.save_minimap_data(self.current_map.name, self.minimap_data)

    def add_end_point(self, point: tuple[int, int]):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            return
        map_editor.add_end_point(point, self.minimap_data)
        map_editor.save_minimap_data(self.current_map.name, self.minimap_data)

    def add_rope_point(self, point: tuple[int, int]):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            return
        map_editor.add_rope_point(point, self.minimap_data)
        map_editor.save_minimap_data(self.current_map.name, self.minimap_data)


shared_map = Map()

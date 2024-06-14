"""A module for saving map layouts and determining shortest paths."""

from src.common.constants import *
from src.common import  utils
from src.common.gui_setting import gui_setting
from src.map import map_editor
from src.models.map_model import MapModel


class Map:
    """Map Manager."""

    def __init__(self):
        self.current_map: MapModel = None
        self.available_maps = [MapModel]
        self._load_data()

    def _load_data(self):
        file_path = f"{RESOURCES_DIR}/maps/maplestory_maps.xlsx"
        map_list = utils.load_excel(file_path)
        available_maps = [MapModel]
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

    def load_map(self, map_name):
        self.clear()
        for map in self.available_maps:
            if map.name == map_name:
                self.current_map = map
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

    def near_rope(self, location: tuple[int, int]):
        if self.data_available:
            height, width = self.minimap_data.shape
            cur_x = location[0]
            cur_y = location[1]
            start_x = max(0, cur_x - 1)
            end_x = min(width - 1, cur_x + 1)
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
                for i in range(0, 7):
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
            height, _ = self.minimap_data.shape
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

    def add_start_point(self, point: tuple[int, int]):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            self.minimap_data = map_editor.create_minimap_data()
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

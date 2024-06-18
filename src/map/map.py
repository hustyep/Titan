"""A module for saving map layouts and determining shortest paths."""

from src.common.constants import *
from src.common import utils
from src.common.gui_setting import gui_setting
from src.map import map_editor
from src.models.map_model import MapModel
from src.modules.capture import capture
from src.common import bot_settings

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

    @property
    def minimap_frame(self):
        if capture.minimap_display is not None and self.current_map is not None:
            return capture.minimap_display[:,
                                           self.current_map.minimap_margin:-self.current_map.minimap_margin]

    def clear(self):
        if self.current_map is not None:
            self.current_map.clear()
            self.current_map = None
            bot_settings.mini_margin = 0
                
    def load_map(self, map_name):
        self.clear()
        for map in self.available_maps:
            if map.name == map_name:
                self.current_map = map
                bot_settings.mini_margin = map.minimap_margin
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
            height, width = self.minimap_data.shape
            cur_x = location[0]
            cur_y = location[1]
            if up:
                start_x = max(0, cur_x - 1)
                end_x = min(width - 1, cur_x + 1)
                start_y = max(0, cur_y - 7)
                end_y = cur_y
                for x in range(start_x, end_x + 1):
                    for y in range(start_y, end_y + 1):
                        if self.point_type((x, y)) == MapPointType.Rope:
                            return True
            else:
                start_x = max(0, cur_x - 1)
                end_x = min(width - 1, cur_x + 1)
                for x in range(start_x, end_x + 1):
                    if self.point_type((x, cur_y + 7)) == MapPointType.FloorRope:
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
            value_l = self.point_type((x - 1, y))
            value_r = self.point_type((x + 1, y))
            return self.is_floor_point(value) and self.is_floor_point(value_l) and self.is_floor_point(value_r)
        else:
            return True

    def platform_point(self, target: tuple[int, int]):
        if self.data_available:
            height, _ = self.minimap_data.shape
            dx = 1
            while True:
                p1 = (target[0], target[1] + dx)
                p2 = (target[0], target[1] - dx)
                if self.point_type(p1) == MapPointType.Unknown and self.point_type(p2) == MapPointType.Unknown:
                    break
                if self.point_type(p1) != MapPointType.Unknown and self.on_the_platform(p1):
                    return p1
                if self.point_type(p2) != MapPointType.Unknown and self.on_the_platform(p2):
                    return p2
                dx += 1
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
            gap = 0
            y = p1[1]
            for x in range(p1[0] + 1, p2[0]):
                if not self.on_the_platform((x, y)):
                    return False
            return True
        else:
            return True

    def add_start_point(self, point: tuple[int, int]):
        if gui_setting.mode.type != BotRunMode.Mapping:
            return
        if not self.data_available:
            self.current_map.minimap_data = map_editor.create_minimap_data(self.minimap_frame)
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

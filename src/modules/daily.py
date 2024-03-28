from src.common.constants import Charactor_Daily_Map
from src.modules.capture import capture
from src.common import utils, bot_status, bot_settings
from src.common.image_template import *

class Daily:

    def __init__(self, role_name: str):
        self.role_name = role_name
        self.quest_list: list[Quest] = []
        self.ready = False
        self.__load_quest()

    def start(self):
        pass

    def pause(self):
        pass

    def __load_quest(self):
        map_list = Charactor_Daily_Map[self.role_name]
        if map_list is not None:
            for map in map_list:
                self.quest_list.add(Quest(map))
        else:
            raise ValueError(f"Invalid daily map list")
        
    def __take_quest(self):
        while has_quest():
            utils.mouse

class Quest:
    def __init__(self, map_name, duration=150):
        self.map_name = map_name
        self.start_time = 0
        self.last_time = 0
        
def has_quest():
    frame = capture.frame[100:-100, 0:200]
    match = utils.multi_match(frame, QUEST_BUBBLE_TEMPLATE)
    return len(match) > 0
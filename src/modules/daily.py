import time

from src.common.constants import Charactor_Daily_Map
from src.modules.capture import capture
from src.common import utils, bot_settings, bot_action, bot_helper
from src.common.image_template import *
from src.common.constants import *


class Daily:

    def __init__(self, role_name: str):
        self.role_name = role_name

        self.quest_list: list[Quest] = []
        self.cur_quest_index = 0
        self.ready = False
        self.__load_quest()

    def start(self):
        if not self.ready:
            self.__take_quest()
        self.__start_quest()

    def pause(self):
        cur_quest = self.quest_list[self.cur_quest_index]
        cur_quest.pause()
        if cur_quest.isDone:
            self.cur_quest_index += 1

    def check(self):
        cur_quest = self.quest_list[self.cur_quest_index]
        if cur_quest.isDone:
            self.cur_quest_index += 1
            self.__start_quest()

    def __load_quest(self):
        map_list = Charactor_Daily_Map[self.role_name]
        if map_list is not None: 
            for map in map_list:
                self.quest_list.append(Quest(map))
        else:
            raise ValueError(f"Invalid daily map list")

    def __take_quest(self):
        while has_quest():
            bot_action.mouse_move(QUEST_BUBBLE_TEMPLATE,
                                  YELLOW_RANGES,
                                  Rect(0, 200, 100, 100))
            bot_action.mouse_left_click(delay=0.3)
            bot_action.click_key(bot_settings.SystemKeybindings.INTERACT, delay=0.3)
            bot_action.click_key('y', delay=0.3)
            bot_action.click_key(bot_settings.SystemKeybindings.INTERACT, delay=0.3)
            bot_action.mouse_move_relative(20, 0)
        self.ready = True

    def __start_quest(self):
        while self.cur_quest_index < len(self.quest_list):
            cur_quest = self.quest_list[self.cur_quest_index]
            if cur_quest.isDone:
                self.cur_quest_index += 1
            else:
                cur_quest.start()
                break


class Quest:
    def __init__(self, map_name: str, duration=150):
        self.map_name = map_name
        self.duration = duration

        self.start_time = 0
        self.last_time = 0

    @property
    def isDone(self):
        if self.last_time >= self.duration:
            return True
        if self.start_time == 0:
            return False
        return self.last_time + time.time() - self.start_time >= self.duration

    def start(self):
        self.__prepare()
        if self.start_time == 0:
            self.start_time = time.time()

    def pause(self):
        if self.start_time == 0:
            return
        self.last_time += time.time() - self.start_time
        self.start_time = 0

    def __prepare(self):
        cur_map_name = bot_helper.identify_map_name()
        if cur_map_name != self.map_name:
            bot_action.teleport_to_map(self.map_name)


def has_quest():
    frame = capture.frame[100:300, 0:200]
    match = utils.multi_match(frame, QUEST_BUBBLE_TEMPLATE)
    return len(match) > 0

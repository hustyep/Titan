"""A module for detecting and notifying the user of dangerous in-game events."""
import time
from datetime import datetime
import threading
import operator
import numpy as np
import win32gui
import win32con
import win32com.client as client
import pythoncom
from rx.subject.subject import Subject

from src.routine.components import Point
from src.routine.routine import routine
from src.common import bot_status, bot_settings
from src.common.image_template import *
from src.common.constants import BotInfo, BotWarnning, BotFatal, BotError, MapPoint, window_cap_horiz, window_cap_botton, window_cap_top
from src.common.hid import hid
from src.modules.capture import capture
from src.map.map import shared_map as game_map
from src.common.gui_setting import gui_setting
from src.common import bot_action, bot_helper
from src.chat_bot.chat_bot import chat_bot


class Detector(Subject):

    def __init__(self):
        """Initializes this Detector object's main thread."""
        super().__init__()

        self.player_pos_updated_time = 0
        self.player_pos = (0, 0)

        self.others_count = 0
        self.others_comming_time = 0
        self.others_detect_count = 0
        self.others_no_detect_count = 0

        self.lost_time_threshold = 1
        self.lost_minimap_time = 0

        self.black_screen_threshold = 0.9
        self.white_room_threshold = 0.35

        self.ready = False
        self.fetal_thread = threading.Thread(target=self._main_fetal)
        self.fetal_thread.daemon = True

        self.exception_thread = threading.Thread(target=self._main_exception)
        self.exception_thread.daemon = True

        self.event_thread = threading.Thread(target=self._main_event)
        self.event_thread.daemon = True

    def start(self):
        """Starts this Detector's thread."""

        print('\n[~] Started detector')
        self.fetal_thread.start()
        self.exception_thread.start()
        self.event_thread.start()

        routine.subscribe(lambda i: self.on_event(i))

        self.ready = True

    def _main_fetal(self):
        while True:
            frame = capture.frame
            if frame is not None:
                self.check_fetal(frame)
            time.sleep(0.1)

    def _main_exception(self):
        while True:
            self.check_minimap()
            if bot_status.enabled and not bot_status.acting:
                self.check_boss()
                self.check_binded()
                self.check_dead()
                # self.check_no_movement()
                self.check_others()
                self.check_alert()
                self.check_forground()
                self.check_init()
            else:
                self.clear()
            time.sleep(0.2)

    def clear(self):
        self.player_pos_updated_time = 0
        self.player_pos = (0, 0)

        self.others_count = 0
        self.others_comming_time = 0
        self.others_detect_count = 0
        self.others_no_detect_count = 0

        self.lost_minimap_time = 0

    def _main_event(self):
        while True:
            frame = capture.frame
            minimap = capture.minimap_frame

            if bot_status.enabled and frame is not None and minimap is not None:
                self.check_rune_status(frame, minimap)
            time.sleep(0.5)

    def on_event(self, args):
        event = args[0]
        if event == BotInfo.RUNE_LIBERATED or BotWarnning.RUNE_FAILED:
            bot_status.rune_pos = None
            bot_status.rune_closest_pos = None

    # check white room
    def check_fetal(self, frame):
        if frame is None:
            return
        height, width, _ = frame.shape
        if width < 400 or height < 400:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Check for unexpected black screen
        # if bot_status.enabled:
        #     if np.count_nonzero(gray < 15) / height / width > self.black_screen_threshold:
        #         self.on_next((BotFatal.BLACK_SCREEN,))

        # Check for white room
        gray_crop = gray[100:-100, 50:-50]
        height, width = gray_crop.shape
        tmp = np.count_nonzero(gray_crop == 255) / height / width
        # print(tmp)
        if bot_status.started_time is not None and tmp >= self.white_room_threshold:
            self.on_next((BotFatal.WHITE_ROOM,))

        # gm = utils.multi_match(frame, GM_HAT_W_TEMPLATE, threshold=0.8)
        # if gm:
        #     self.on_next((BotFatal.WHITE_ROOM,))

    def check_alert(self):
        if capture.frame is None:
            return
        frame = capture.frame

        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 220) // 2
        ok_btn = utils.multi_match(
            frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)
        if ok_btn:
            hid.key_press('esc')
            time.sleep(0.1)
            return

        x = (frame.shape[1] - 520) // 2
        y = (frame.shape[0] - 400) // 2
        end_talk = utils.multi_match(
            frame[y:y+400, x:x+520], END_TALK_TEMPLATE, threshold=0.8)
        if end_talk:
            hid.key_press('esc')
            time.sleep(0.1)
            return
        confirm_btn = utils.multi_match(
            frame[y:y+400, x:x+520], BUTTON_CONFIRM_TEMPLATE, threshold=0.8)
        if confirm_btn:
            hid.key_press('esc')
            time.sleep(0.1)

        chat_btn = utils.multi_match(
            frame, CHAT_MINI_TEMPLATE, threshold=0.9)
        if chat_btn:
            bot_action.mouse_left_click(
                bot_helper.get_full_pos(chat_btn[0]), delay=0.5)

        setting_btn = utils.multi_match(
            frame[400:600, 800:1000], SETTING_TEMPLATE, threshold=0.9)
        if setting_btn:
            hid.key_press('esc')
            time.sleep(0.1)

        inventory = utils.multi_match(frame, INVENTORY_MESO_TEMPLATE)
        if inventory:
            hid.key_press('esc')
            time.sleep(0.1)

    def check_init(self):
        if capture.frame is None:
            return
        frame = capture.frame
        guide = utils.multi_match(
            frame[0:150, ], GUIDE_PLUSE_TEMPLATE, threshold=0.9)
        if guide:
            hid.key_press('esc')
            time.sleep(1)
            # ActionSimulator.mouse_left_click(position=get_full_pos(853, 52), delay=0.1)

        maple_reward = utils.multi_match(
            frame[-200:, -50:], MAPLE_REWARD_TEMPLATE, threshold=0.9)
        if maple_reward:
            bot_action.mouse_left_click(
                bot_helper.get_full_pos((1351, 586)), delay=1)

        adv = utils.multi_match(
            frame[190:200, 1000:1100], ADV_CLOSE_TEMPLATE, threshold=0.9)
        if adv:
            bot_action.mouse_left_click(
                bot_helper.get_full_pos(adv[0]), delay=1)

        today = datetime.now().weekday()
        if today == 6:
            sunday = utils.multi_match(
                frame[180:235, 630:700], SUNNY_SUNDAY_TEMPLATE, threshold=0.9)
            if sunday:
                bot_action.mouse_left_click(
                    bot_helper.get_full_pos((890, 330)), delay=1)

    def check_forground(self):
        frame = capture.camera.get_latest_frame()
        if frame is None:
            return
        capture.find_window()
        hwnd = capture.hwnd
        if (hwnd == 0):
            self.on_next((BotError.LOST_WINDOW, ))
            return

        '''Check if window is forground'''
        if hwnd != win32gui.GetForegroundWindow():
            self.on_next((BotWarnning.BACKGROUND, ))
            mathes = utils.multi_match(
                frame[-50:, ], TABBAR_MAPLE_TEMPLATE, threshold=0.9)
            if mathes:
                height = frame.shape[0]
                bot_action.mouse_left_click(
                    (mathes[0][0], height - 25), delay=1)
            # try:
            #     pythoncom.CoInitialize()
            #     shell = client.Dispatch("WScript.Shell")
            #     shell.SendKeys('%')
            #     if win32gui.IsIconic(capture.hwnd):
            #         win32gui.SendMessage(
            #             capture.hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
            #         time.sleep(0.1) 
            #     win32gui.SetForegroundWindow(capture.hwnd)
            # except Exception as e:
            #     print(e)
            # time.sleep(0.5)

    def check_minimap(self):
        capture.find_window()
        if capture.hwnd == 0:
            return
        x1, y1, x2, y2 = win32gui.GetWindowRect(capture.hwnd)  # 获取当前窗口大小
        if x1 != 0:
            x1 += window_cap_horiz
            x2 -= window_cap_horiz
            y1 += window_cap_top
            y2 -= window_cap_botton
        tl = dll_helper.screenSearch(MM_TL_BMP, x1, y1, x2, y2)
        br = dll_helper.screenSearch(MM_BR_BMP,  x1, y1, x2, y2)
        if tl == None or br == None:
            bot_status.lost_minimap = True
            capture.calibrated = False
            if bot_status.enabled and not bot_status.acting:
                if self.lost_minimap_time == 0:
                    self.lost_minimap_time = time.time()
                if time.time() - self.lost_minimap_time > self.lost_time_threshold:
                    self.on_next(
                        (BotError.LOST_MINI_MAP, time.time() - self.lost_minimap_time))
            else:
                self.lost_minimap_time = 0
        else:
            self.lost_minimap_time = 0
            bot_status.lost_minimap = False

    # def try_auto_login(self):
    #     bot_status.enabled = False

    #     for _ in range(0, 10):
    #         capture.find_window()
    #         hwnd = capture.hwnd
    #         if (hwnd == 0):
    #             self.on_next((BotError.LOST_WINDOW, ))
    #             return True

    #         region_matchs = utils.multi_match(
    #             capture.frame, BUTTON_CHANGE_REGION_TEMPLATE, threshold=0.9)
    #         if region_matchs:
    #             chat_bot.send_message('disconnected...')
    #             bot_action.auto_login(gui_setting.auto.auto_login_channel)
    #             return True
    #         time.sleep(0.5)
    #     else:
    #         return False

    def check_no_movement(self):
        if bot_status.enabled and operator.eq(bot_status.player_pos, self.player_pos):
            interval = int(time.time() - self.player_pos_updated_time)
            if interval >= 15 and self.player_pos_updated_time:
                self.on_next((BotWarnning.NO_MOVEMENT, interval))
        else:
            self.player_pos = bot_status.player_pos
            self.player_pos_updated_time = time.time()

    def check_boss(self):
        frame = capture.frame
        if frame is None:
            return
        height, width, _ = frame.shape
        elite_frame = frame[height // 4:3 *
                            height // 4, width // 4:3 * width // 4]
        elite = utils.multi_match(elite_frame, ELITE_TEMPLATE, threshold=0.9)
        if len(elite) > 0:
            self.on_next((BotInfo.BOSS_APPEAR, ))

    def check_binded(self):
        frame = capture.frame
        if frame is None:
            return
        player_template = bot_settings.role.name_template
        player = utils.multi_match(
            frame, player_template, threshold=0.9)
        if len(player) == 0:
            return
        player_pos = player[0]
        crop = frame[player_pos[1]-140:player_pos[1] -
                     100, player_pos[0]+25:player_pos[0]+65]
        res = utils.multi_match(crop, SKULL_TEMPLATE)
        if len(res) > 0:
            self.on_next((BotWarnning.BINDED, ))

            bot_status.acting = True
            while (len(res) > 0):
                for _ in range(4):
                    hid.key_press('left')
                    hid.key_press("right")
                if capture.frame is None:
                    break
                crop = capture.frame[player_pos[1]-140:player_pos[1] -
                                     100, player_pos[0]+25:player_pos[0]+65]
                res = utils.multi_match(crop, SKULL_TEMPLATE)
            bot_status.acting = False

    # Check for dead
    def check_dead(self):
        frame = capture.frame
        if frame is None:
            return
        x = (frame.shape[1] - 450) // 2
        y = (frame.shape[0] - 200) // 2
        image = frame[y:y+200, x:x+450]
        tombstone = utils.multi_match(
            image, DEAD_TOBBSTONE_TEMPLATE, threshold=0.85)
        if tombstone:
            ok_btn = utils.multi_match(
                image, DEAD_OK_TEMPLATE, threshold=0.7)
            if ok_btn:
                hid.mouse_abs_move(capture.window['left'] + ok_btn[0][0] + x,
                                   capture.window['top'] + ok_btn[0][1] + y)
                time.sleep(1)
                hid.mouse_left_click()
                time.sleep(1)
                hid.mouse_left_click()
            self.on_next((BotError.DEAD, ))

    def check_others(self):
        if game_map.current_map is None or game_map.current_map.instance:
            return
        minimap = capture.minimap_display
        filtered = utils.filter_color(minimap, OTHER_RANGES)
        others = len(utils.multi_match(
            filtered, OTHER_TEMPLATE, threshold=0.7))

        guild_filtered = utils.filter_color(minimap, GUILDMATE_RANGES)
        guildmates = len(utils.multi_match(
            guild_filtered, GUILDMATE_TEMPLATE, threshold=0.7))

        others += guildmates

        bot_status.stage_fright = others > 0

        self.others_count = others
        # print(f"others:{others} | others_detect_count:{self.others_detect_count} | others_no_detect_count:{self.others_no_detect_count}")
        if others > 0:
            self.others_detect_count += 1
            self.others_no_detect_count = 0
            if self.others_comming_time == 0:
                self.others_comming_time = time.time()
        else:
            self.others_no_detect_count += 1

        duration = int(time.time() - self.others_comming_time)
        if self.others_no_detect_count == 30:
            self.others_no_detect_count += 1
            if self.others_comming_time > 0 and self.others_detect_count > 40:
                self.on_next((BotInfo.OTHERS_LEAVED, ))
            self.others_detect_count = 0
            self.others_comming_time = 0
        elif self.others_detect_count == 2000:
            self.others_detect_count += 1
            self.on_next((BotError.OTHERS_STAY_OVER_120S, duration))
        elif self.others_detect_count == 200:
            self.others_detect_count += 1
            self.on_next((BotWarnning.OTHERS_STAY_OVER_60S, duration))
        elif self.others_detect_count == 100:
            self.others_detect_count += 1
            self.on_next((BotWarnning.OTHERS_STAY_OVER_30S, duration))
        elif self.others_detect_count == 50:
            self.others_detect_count += 1
            self.on_next((BotWarnning.OTHERS_COMMING, duration))

    def check_rune_status(self, frame, minimap):
        if bot_status.rune_solving:
            return

        if frame is None or minimap is None:
            bot_status.rune_pos = None
            bot_status.rune_closest_pos = None
            return

        rune_buff = utils.multi_match(
            frame[:150, :], RUNE_BUFF_TEMPLATE[1:11, -15:-1], threshold=0.9)
        if len(rune_buff) == 0:
            rune_buff = utils.multi_match(
                frame[:150, :], RUNE_BUFF_GRAY_TEMPLATE, threshold=0.8)
        if rune_buff:
            bot_status.rune_pos = None
            bot_status.rune_closest_pos = None
            return

        filtered = utils.filter_color(minimap, RUNE_RANGES)
        matches = utils.multi_match(filtered, RUNE_TEMPLATE, threshold=0.9)
        if len(matches) == 0:
            return

        if routine.sequence:
            old_pos = bot_status.rune_pos
            abs_rune_pos = game_map.platform_point(
                MapPoint(matches[0][0], matches[0][1], 1))
            if old_pos != abs_rune_pos:
                bot_status.rune_pos = abs_rune_pos
                distances = list(
                    map(distance_to_rune, routine.sequence))
                index = np.argmin(distances)
                # bot_status.rune_closest_pos = routine[index].location
                self.on_next((BotInfo.RUNE_ACTIVE, ))


detector = Detector()


#################################
#       Helper Functions        #
#################################


def distance_to_rune(point):
    """
    Calculates the distance from POINT to the rune.
    :param point:   The position to check.
    :return:        The distance from POINT to the rune, infinity if it is not a Point object.
    """

    if isinstance(point, Point) and point.interval == 0 and point.parent is None and bot_status.rune_pos is not None:
        return utils.distance(bot_status.rune_pos.tuple, point.location)
    return float('inf')

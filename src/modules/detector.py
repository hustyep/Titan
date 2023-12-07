"""A module for detecting and notifying the user of dangerous in-game events."""

import time
import string
import threading
import operator
import numpy as np
import win32gui
import win32con
import win32com.client as client
import win32gui
import win32con
import win32com.client as client
import pythoncom
from rx.subject import Subject

from src.routine.components import Point
from src.routine.routine import routine
from src.common import bot_status, bot_settings
from src.common.image_template import *
from src.common.constants import *
from src.common.hid import hid
from src.modules.capture import capture
from src.map.map import map as game_map
from src.common.gui_setting import gui_setting
from src.common.action_simulator import ActionSimulator

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
        self.white_room_threshold = 0.6

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
            if bot_status.enabled:
                # self.check_boss()
                # self.check_binded()
                self.check_dead()
                self.check_no_movement()
                # self.check_others()
                self.check_alert()
                self.check_forground()
            else:
                self.clear()
            time.sleep(0.1)

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
            minimap = capture.minimap_actual

            if bot_status.enabled and frame is not None and minimap is not None:
                self.check_rune_status(frame, minimap)
                self.check_mineral(frame, minimap)
            time.sleep(0.5)

    def on_event(self, args):
        event = args[0]
        if event == BotInfo.RUNE_LIBERATED:
            bot_status.rune_pos = None
            bot_status.rune_closest_pos = None

    # check white room
    def check_fetal(self, frame):
        if frame is None:
            return
        height, width, _ = frame.shape
        if width < 400 and height < 400:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Check for unexpected black screen
        if bot_status.enabled:
            if np.count_nonzero(gray < 15) / height / width > self.black_screen_threshold:
                self.on_next((BotFatal.BLACK_SCREEN,))

        # Check for white room
        gray_crop = gray[100:-100, 50:-50]
        height, width = gray.shape
        if bot_status.started_time and np.count_nonzero(gray_crop == 255) / height / width >= self.white_room_threshold:
            self.on_next((BotFatal.WHITE_ROOM,))

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
            frame[y:y+400, x:x+520], END_TALK_TEMPLATE, threshold=0.9)
        if end_talk:
            hid.key_press('esc')
            time.sleep(0.1)
            return
        confirm_btn = utils.multi_match(
            frame[y:y+400, x:x+520], BUTTON_CONFIRM_TEMPLATE, threshold=0.9)
        if confirm_btn:
            hid.key_press('esc')
            time.sleep(0.1)

    def check_forground(self):
        if capture.frame is None:
            return
        capture.find_window()
        hwnd = capture.hwnd
        if (hwnd == 0):
            self.on_next((BotError.LOST_WINDOW, ))
            return

        '''Check if window is forground'''
        if hwnd != win32gui.GetForegroundWindow():
            self.on_next((BotWarnning.BACKGROUND, ))
            try:
                pythoncom.CoInitialize()
                shell = client.Dispatch("WScript.Shell")
                shell.SendKeys('%')
                if win32gui.IsIconic(capture.hwnd):
                    win32gui.SendMessage(
                        capture.hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
                    time.sleep(0.1)
                win32gui.SetForegroundWindow(capture.hwnd)
            except Exception as e:
                print(e)
            time.sleep(0.5)

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
            if bot_status.enabled:
                if self.lost_minimap_time == 0:
                    self.lost_minimap_time = time.time()
                if time.time() - self.lost_minimap_time > self.lost_time_threshold:
                    # if not self.try_auto_login():
                    self.on_next(
                        (BotError.LOST_MINI_MAP, time.time() - self.lost_minimap_time))
        else:
            self.lost_minimap_time = 0
            bot_status.lost_minimap = False

    def try_auto_login(self):
        bot_status.enabled = False
        
        for _ in range(0, 16):
            capture.find_window()
            hwnd = capture.hwnd
            if (hwnd == 0):
                self.on_next((BotError.LOST_WINDOW, ))
                return True
        
            region_matchs = utils.multi_match(
                capture.frame, BUTTON_CHANGE_REGION_TEMPLATE, threshold=0.95)
            if region_matchs:
                ActionSimulator.auto_login()
                return True
            time.sleep(0.5)
        else:
            return False

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
            self.on_next((BotVerbose.BOSS_APPEAR, ))

    def check_binded(self):
        frame = capture.frame
        if frame is None:
            return
        player_template = bot_settings.role_template
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

            bot_status.enabled = False
            while (len(res) > 0):
                for _ in range(4):
                    hid.key_press('left')
                    hid.key_press("right")
                if capture.frame is None:
                    break
                crop = capture.frame[player_pos[1]-140:player_pos[1] -
                                     100, player_pos[0]+25:player_pos[0]+65]
                res = utils.multi_match(crop, SKULL_TEMPLATE)
            bot_status.enabled = True

    # Check for dead
    def check_dead(self):
        frame = capture.frame
        if frame is None:
            return
        x = (frame.shape[1] - 450) // 2
        y = (frame.shape[0] - 200) // 2
        image = frame[y:y+200, x:x+450]
        tombstone = utils.multi_match(
            image, DEAD_TOBBSTONE_TEMPLATE, threshold=0.9)
        if tombstone:
            self.on_next((BotError.DEAD, ))
            ok_btn = utils.multi_match(
                image, DEAD_OK_TEMPLATE, threshold=0.9)
            if ok_btn:
                hid.mouse_abs_move(capture.window['left'] + ok_btn[0][0] + x,
                                   capture.window['top'] + ok_btn[0][1] + y)
                time.sleep(1)
                hid.mouse_left_click()
                time.sleep(1)
                hid.mouse_left_click()

    def check_others(self):
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
        # elif self.others_detect_count == 200:
        #     self.others_detect_count += 1
        #     self.on_next((BotWarnning.OTHERS_STAY_OVER_60S, duration))
        # elif self.others_detect_count == 100:
        #     self.others_detect_count += 1
        #     self.on_next((BotWarnning.OTHERS_STAY_OVER_30S, duration))
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

        filtered = utils.filter_color(minimap, RUNE_RANGES)
        matches = utils.multi_match(filtered, RUNE_TEMPLATE, threshold=0.9)
        if len(matches) == 0:
            bot_status.rune_pos = None
            bot_status.rune_closest_pos = None
            return

        rune_buff = utils.multi_match(
            frame[:150, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
        if len(rune_buff) == 0:
            rune_buff = utils.multi_match(
                frame[:150, :], RUNE_BUFF_GRAY_TEMPLATE, threshold=0.9)
        if rune_buff:
            bot_status.rune_pos = None
            bot_status.rune_closest_pos = None
            return

        if routine.sequence:
            old_pos = bot_status.rune_pos
            abs_rune_pos = game_map.platform_point(
                (matches[0][0], matches[0][1]))
            if old_pos != abs_rune_pos:
                bot_status.rune_pos = abs_rune_pos
                distances = list(
                    map(distance_to_rune, routine.sequence))
                index = np.argmin(distances)
                bot_status.rune_closest_pos = routine[index].location
                self.on_next((BotInfo.RUNE_ACTIVE, ))

    def check_mineral(self, frame, minimap):
        if not gui_setting.auto.mining:
            return

        if frame is None or minimap is None:
            return

        if bot_status.minal_pos:
            return

        player_min = utils.multi_match(minimap, PLAYER_TEMPLATE, threshold=0.8)
        if len(player_min) == 0:
            return
        player_pos = player_min[0]

        matches = utils.multi_match(frame, MINAL_HEART_TEMPLATE)
        mineral_type = MineralType.HEART
        if len(matches) == 0:
            matches = utils.multi_match(frame, HERB_YELLOW_TEMPLATE)
            mineral_type = MineralType.HERB_YELLOW
        if len(matches) == 0:
            matches = utils.multi_match(frame, HERB_PURPLE_TEMPLATE)
            mineral_type = MineralType.HERB_PURPLE
        if len(matches) == 0:
            matches = utils.multi_match(frame, MINAL_CRYSTAL_TEMPLATE)
            mineral_type = MineralType.CRYSTAL
        if len(matches) > 0:
            self.on_next((BotVerbose.MINE_ACTIVE, mineral_type))
            player_template = bot_settings.role_template
            player = utils.multi_match(
                frame, player_template, threshold=0.9)
            if len(player) > 0:
                bot_status.mineral_type = mineral_type
                minal_full_pos = matches[0]
                if mineral_type == MineralType.HERB_YELLOW:
                    minal_full_pos = (
                        minal_full_pos[0] - 18, minal_full_pos[1] - 70)
                elif mineral_type == MineralType.HERB_PURPLE:
                    minal_full_pos = (
                        minal_full_pos[0] - 18, minal_full_pos[1] - 40)
                elif mineral_type == MineralType.CRYSTAL:
                    minal_full_pos = (
                        minal_full_pos[0] - 10, minal_full_pos[1] - 50)
                elif mineral_type == MineralType.HEART:
                    minal_full_pos = (
                        minal_full_pos[0] - 10, minal_full_pos[1] - 60)

                player_full_pos = player[0]
                dx_full = minal_full_pos[0] - player_full_pos[0]
                dy_full = minal_full_pos[1] - (player_full_pos[1] - 130)
                minal_pos = (
                    player_pos[0] + round(dx_full / 15.0), player_pos[1] + round(dy_full / 15.0))
                bot_status.minal_pos = minal_pos
                distances = list(
                    map(distance_to_minal, routine.sequence))
                index = np.argmin(distances)
                bot_status.minal_closest_pos = routine[index].location

    def identify_role(self):
        role_name = ''
        class_name = ''

        name = utils.image_2_str(capture.name_frame).replace(
            " ", "").replace('\n', '').lower()

        best = 0
        for key, value in Name_Class_Map.items():
            ratio = utils.string_similar(name, key.lower())
            if ratio == 1:
                class_name = value
                role_name = key
                break
            elif ratio > best:
                best = ratio
                class_name = value
                role_name = key

        return role_name, class_name

    def identify_map_name(self):
        frame = utils.filter_color(capture.map_name_frame, TEXT_WHITE_RANGES)
        # utils.show_image(frame)
        name = utils.image_2_str(frame).replace('\n', '')
        for i in string.punctuation:
            if i not in ['-']:
                name = name.replace(i, '')
        result = name
        best = 0
        for value in Map_Names:
            ratio = utils.string_similar(name, value)
            if ratio == 1:
                result = value
                break
            elif ratio > best:
                best = ratio
                result = value
        return result


detector = Detector()


def exception_hook(exc_type, exc_value, tb):
    print('Traceback:')
    filename = tb.tb_frame.f_code.co_filename
    name = tb.tb_frame.f_code.co_name
    line_no = tb.tb_lineno
    info = (
        f"File {filename} line {line_no}, in {name}\n"
        f"{exc_type.__name__}, Message: {exc_value}\n"
    )
    detector.on_next((BotFatal.CRASH, info))

    print(f"File {filename} line {line_no}, in {name}")

    # Exception type 和 value
    print(f"{exc_type.__name__}, Message: {exc_value}")


# sys.excepthook = exception_hook

#################################
#       Helper Functions        #
#################################


def distance_to_rune(point):
    """
    Calculates the distance from POINT to the rune.
    :param point:   The position to check.
    :return:        The distance from POINT to the rune, infinity if it is not a Point object.
    """

    if isinstance(point, Point) and point.interval == 0 and point.parent is None:
        return utils.distance(bot_status.rune_pos, point.location)
    return float('inf')


def distance_to_minal(point):
    """
    Calculates the distance from POINT to the minal.
    :param point:   The position to check.
    :return:        The distance from POINT to the minal, infinity if it is not a Point object.
    """

    if isinstance(point, Point) and point.interval == 0:
        return utils.distance(bot_status.minal_pos, point.location)
    return float('inf')

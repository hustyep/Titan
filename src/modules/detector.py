"""A module for detecting and notifying the user of dangerous in-game events."""

import time
import threading
import operator
import numpy as np
import os
import sys
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

        self.black_screen_threshold = 0.9
        self.white_room_threshold = 0.55

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

        routine.subscribe(lambda i:self.on_event(i))

        self.ready = True

    def _main_fetal(self):
        while True:
            frame = capture.frame
            if frame is not None:
                self.check_fetal(frame)
            time.sleep(0.2)

    def _main_exception(self):
        while True:
            frame = capture.frame

            if bot_status.enabled and frame is not None:
                self.check_boss(frame)
                self.check_binded(frame)
                self.check_dead(frame)
                self.check_no_movement()
                self.check_others()
                self.check_forground()
            time.sleep(0.2)

    def _main_event(self):
        while True:
            frame = capture.frame
            minimap = capture.minimap_actual

            if bot_status.enabled and frame is not None and minimap is not None:
                self.check_rune_status(frame, minimap)
                self.check_mineral(frame, minimap)
            time.sleep(0.2)

    def on_event(self, args):
        event = args[0]
        if event == BotInfo.RUNE_LIBERATED:
            self.rune_active_time = 0
            bot_status.rune_pos = None
        
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

    def check_alert(self, frame):
        if frame is None:
            return

        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 220) // 2
        ok_btn = utils.multi_match(
            frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)

        x = (frame.shape[1] - 520) // 2
        y = (frame.shape[0] - 400) // 2
        end_talk = utils.multi_match(
            frame[y:y+400, x:x+520], END_TALK_TEMPLATE, threshold=0.9)
        if ok_btn or end_talk:
            hid.key_press('esc')
            time.sleep(0.1)

    def check_forground(self):
        '''Check if window is forground'''
        if capture.hwnd and capture.hwnd != win32gui.GetForegroundWindow():
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

    def check_no_movement(self):
        if bot_status.enabled and operator.eq(bot_status.player_pos, self.player_pos):
            interval = int(time.time() - self.player_pos_updated_time)
            if interval >= 15 and self.player_pos_updated_time:
                self.on_next((BotWarnning.NO_MOVEMENT, interval))
        else:
            self.player_pos = bot_status.player_pos
            self.player_pos_updated_time = time.time()

    def check_boss(self, frame):
        height, width, _ = frame.shape
        elite_frame = frame[height // 4:3 *
                            height // 4, width // 4:3 * width // 4]
        elite = utils.multi_match(elite_frame, ELITE_TEMPLATE, threshold=0.9)
        if len(elite) > 0:
            self.on_next((BotVerbose.BOSS_APPEAR, ))

    def check_binded(self, frame):
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
    def check_dead(self, frame):
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
        if self.others_no_detect_count == 150:
            self.others_no_detect_count += 1
            if self.others_comming_time > 0 and self.others_detect_count > 200:
                self.on_next((BotInfo.OTHERS_LEAVED, ))
            self.others_detect_count = 0
            self.others_comming_time = 0
        elif self.others_detect_count == 1200:
            self.others_detect_count += 1
            self.on_next((BotError.OTHERS_STAY_OVER_120S, duration))
        elif self.others_detect_count == 800:
            self.others_detect_count += 1
            self.on_next((BotWarnning.OTHERS_STAY_OVER_60S, duration))
        elif self.others_detect_count == 500:
            self.others_detect_count += 1
            self.on_next((BotWarnning.OTHERS_STAY_OVER_30S, duration))
        elif self.others_detect_count == 200:
            self.others_detect_count += 1
            self.on_next((BotWarnning.OTHERS_COMMING, duration))

    def check_rune_status(self, frame, minimap):
        if frame is None or minimap is None:
            bot_status.rune_pos = None
            self.rune_active_time = 0
            return

        filtered = utils.filter_color(minimap, RUNE_RANGES)
        matches = utils.multi_match(filtered, RUNE_TEMPLATE, threshold=0.9)
        if len(matches) == 0:
            return

        if routine.sequence:
            old_pos = bot_status.rune_pos
            abs_rune_pos = (matches[0][0], matches[0][1])
            if old_pos != abs_rune_pos:
                bot_status.rune_pos = abs_rune_pos
                distances = list(
                    map(distance_to_rune, routine.sequence))
                index = np.argmin(distances)
                bot_status.rune_closest_pos = routine[index].location
                self.on_next((BotInfo.RUNE_ACTIVE, ))

    def check_mineral(self, frame, minimap):
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

    if isinstance(point, Point) and point.interval == 0:
        return utils.distance(bot_status.rune_pos, point.location)
    return float('inf')


def distance_to_minal(point):
    """
    Calculates the distance from POINT to the minal.
    :param point:   The position to check.
    :return:        The distance from POINT to the minal, infinity if it is not a Point object.
    """

    if isinstance(point, Point):
        return utils.distance(bot_status.minal_pos, point.location)

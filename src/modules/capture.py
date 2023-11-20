import ctypes
import threading
import time
import operator
import dxcam
import win32gui

from enum import Enum
from rx.subject import Subject

from src.common.dll_helper import dll_helper
from src.common.image_template import MM_TL_BMP, MM_BR_BMP, PLAYER_TEMPLATE, PLAYER_TEMPLATE_L, PLAYER_TEMPLATE_R
from src.common import utils, bot_status, bot_settings
from src.common.constants import *

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

class Capture(Subject):

    def __init__(self):
        super().__init__()

        self.camera = dxcam.create(output_idx=0, output_color="BGR")
        self.calibrated = False
        self.window_list = []
        self.hwnd = 0
        self.msg_hwnd = 0
        self.frame = None
        self.msg_frame = None
        self.minimap_actual = None
        self.minimap_display = None
        self.window = {
            'left': 0,
            'top': 0,
            'width': 1366,
            'height': 768
        }
        self.msg_window = (0, 0, 0, 0)
        self.mm_tl = None
        self.mm_br = None

        self.lost_player_time = 0

        self.lost_time_threshold = 1

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Capture's thread."""
        self.camera.start(video_mode=False)

        self.thread.start()
        print('\n[~] Started video capture')

        self.ready = True

    def _main(self):
        """Constantly monitors the player's position and in-game events."""
        while True:
            self.calibrated = self.recalibrate()
            if not self.calibrated:
                time.sleep(0.1)
                continue

            while True:
                if not self.calibrated:
                    break
                self.locatePlayer()

    def emum_windows_callback(self, hwnd, window_list):
        title = win32gui.GetWindowText(hwnd)
        if title == 'MapleStory' and not hwnd in window_list:
            # class_name = win32gui.GetClassName(hwnd)
            # print('title:', title, 'name:', class_name)
            window_list.append(hwnd)

    def find_window(self):
        self.window_list.clear()
        win32gui.EnumWindows(self.emum_windows_callback, self.window_list)
        if len(self.window_list) > 1:
            self.hwnd = self.window_list[-1]
            self.msg_hwnd = self.window_list[0]
        elif self.window_list:
            self.hwnd = self.window_list[0]
        else:
            self.hwnd = 0
            self.msg_hwnd = 0

    def calibrate_msg_window(self):
        if not self.msg_hwnd:
            return
        self.msg_window = win32gui.GetWindowRect(self.msg_hwnd)  # 获取当前窗口大小

    def recalibrate(self):
        self.find_window()
        self.calibrate_msg_window()
        
        ''' Calibrate screen capture'''
        # self.hwnd = win32gui.FindWindow(None, "MapleStory")
        if not self.hwnd:
            if bot_status.enabled:
                self.on_next((BotError.LOST_WINDOW, ))
            return False

        x1, y1, x2, y2 = win32gui.GetWindowRect(self.hwnd)  # 获取当前窗口大小
        if x1 != 0:
            x1 += window_cap_horiz
            x2 -= window_cap_horiz
            y1 += window_cap_top
            y2 -= window_cap_botton

        self.window['left'] = x1
        self.window['top'] = y1
        self.window['width'] = x2 - x1
        self.window['height'] = y2 - y1

        # Calibrate by finding the top-left and bottom-right corners of the minimap
        tl = dll_helper.screenSearch(MM_TL_BMP, x1, y1, x2, y2)
        br = dll_helper.screenSearch(MM_BR_BMP,  x1, y1, x2, y2)

        if tl == None or br == None:
            bot_status.lost_minimap = True
            return False

        bot_status.lost_minimap = False
        mm_tl = (
            tl[0] - x1 - 2,
            tl[1] - y1 + 2
        )
        mm_br = (
            br[0] - x1 + 16,
            br[1] - y1
        )

        if operator.eq(mm_tl, self.mm_tl) and operator.eq(mm_br, self.mm_br):
            return True

        self.mm_tl = mm_tl
        self.mm_br = mm_br

        return True

    def locatePlayer(self):
        frame = self.camera.get_latest_frame()
        if frame is None:
            return

        top = self.window['top']
        left = self.window['left']
        width = self.window['width']
        height = self.window['height']
        new_frame = frame[top:top+height, left:left+width]

        # Crop the frame to only show the minimap
        minimap = new_frame[self.mm_tl[1]
            :self.mm_br[1], self.mm_tl[0]:self.mm_br[0]]

        # Determine the player's position
        player = utils.multi_match(minimap, PLAYER_TEMPLATE, threshold=0.8)
        if len(player) == 0:
            player = utils.multi_match(
                minimap, PLAYER_TEMPLATE_R, threshold=0.8)
            if player:
                x = player[0][0] - 2
                y = player[0][1]
                player[0] = (x, y)
        if len(player) == 0:
            player = utils.multi_match(
                minimap, PLAYER_TEMPLATE_L, threshold=0.8)
            if player:
                x = player[0][0] + 2
                y = player[0][1]
                player[0] = (x, y)

        if player:
            # h, w, _ = minimap.shape
            # print(f"{player[0]} | {w}")
            bot_status.player_pos = self.convert_to_relative_minimap_point(
                player[0])
            self.lost_player_time = 0
        else:
            self.calibrated = False
            if bot_status.enabled:
                now = time.time()
                if self.lost_player_time == 0:
                    self.lost_player_time = now
                if now - self.lost_player_time >= self.lost_time_threshold:
                    self.on_next(
                        (BotError.LOST_PLAYER, now - self.lost_player_time))

        self.frame = new_frame
        if len(self.window_list) > 1:
            self.msg_frame = frame[self.msg_window[1]:self.msg_window[3], self.msg_window[0]:self.msg_window[2]]
        self.minimap_display = minimap
        self.minimap_actual = minimap[:,
                                      bot_settings.mini_margin:-bot_settings.mini_margin]
        self.on_next((BotVerbose.NEW_FRAME, self.frame))

    def convert_to_relative_minimap_point(self, pos: tuple[int, int]):
        return (pos[0] - bot_settings.mini_margin, pos[1])

    def convert_to_absolute_minimap_point(self, pos: tuple[int, int]):
        if not pos:
            return None
        return (pos[0] + bot_settings.mini_margin, pos[1])

    def convert_point_minimap_to_window(self, point: tuple[int, int]):
        '''convent the minimap point to the window point'''
        window_width = self.window['width']
        window_height = self.window['height']

        mini_height, mini_width, _ = self.minimap_actual.shape

        map_width = mini_width * MINIMAP_SCALE
        map_height = mini_height * MINIMAP_SCALE

        map_x = point[0] * MINIMAP_SCALE
        map_y = point[1] * MINIMAP_SCALE

        if map_x < window_width // 2:
            x = map_x
        elif map_width - map_x < window_width // 2:
            x = map_x - (map_width - window_width)
        else:
            x = window_width // 2

        if map_y < window_height // 2:
            y = map_y
        elif map_height - map_y < window_height // 2:
            y = map_y - (map_height - window_height)
        else:
            y = window_height // 2
        return (int(x), int(y))

    def locate_player_fullscreen(self, accurate=False, frame=None, role_template=None):# -> tuple | tuple[int, int]:
        player_pos = self.convert_point_minimap_to_window(
            bot_status.player_pos)

        if accurate:
            if frame is None:
                frame = self.frame
            if role_template is None:
                role_template = bot_settings.role_template
            tl_x = player_pos[0]-50
            tl_y = player_pos[1]
            player_crop = frame[tl_y:tl_y+250, tl_x-150:tl_x+150]
            matchs = utils.multi_match(player_crop,
                                       role_template,
                                       threshold=0.9,
                                       debug=False)
            if matchs:
                player_pos = (matchs[0][0] - 5 + tl_x,
                              matchs[0][1] - 140 + tl_y)
        return player_pos

    @property
    def buff_frame(self):
        if self.frame is not None:
            return self.frame[:150, ]

    @property
    def skill_frame(self):
        if self.frame is not None:
            return self.frame[-200:, -600:]

    @property
    def name_frame(self):
        if self.frame is not None:
            width = self.frame.shape[1]
            return self.frame[-80:-55, (width - 30)//2:(width + 80)//2]

    @property
    def map_name_frame(self):
        if self.frame is not None:
            return self.frame[self.mm_tl[1] - 28:self.mm_tl[1] - 10,
                            self.mm_tl[0] + 36:self.mm_br[0]]


capture = Capture()

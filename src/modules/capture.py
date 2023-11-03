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
from src.common import utils, bot_status

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()


class CaptureExceptionType(Enum):
    LOST_PLAYER = 'Lost Player'
    LOST_WINDOW = 'Lost Window'
    LOST_MINI_MAP = 'Lost Minimap'


class CaptureException(Exception):
    def __init__(self, type: CaptureExceptionType, last: int):
        self.type = type
        self.last = last


class Capture(Subject):

    def __init__(self):
        self.camera = dxcam.create(output_idx=0, output_color="BGR")
        self.calibrated = False
        self.hwnd = None
        self.frame = None
        self.window = {
            'left': 0,
            'top': 0,
            'width': 1366,
            'height': 768
        }

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
            self.calibrated = self.calibrate()
            if not self.calibrated:
                time.sleep(0.1)
                continue

            while True:
                if not self.calibrated:
                    break
                self.locatePlayer()

    def calibrate(self):
        ''' Calibrate screen capture'''
        self.hwnd = win32gui.FindWindow(None, "MapleStory")
        if (self.hwnd == 0):
            now = time.time()
            if self.lost_window_time == 0:
                self.lost_window_time = now
            self.on_error(CaptureException(
                CaptureExceptionType.LOST_WINDOW, now - self.lost_window_time))
            return False

        self.lost_window_time = 0
        x1, y1, x2, y2 = win32gui.GetWindowRect(self.hwnd)  # 获取当前窗口大小

        self.window['left'] = x1
        self.window['top'] = y1
        self.window['width'] = x2 - x1
        self.window['height'] = y2 - y1

        # Calibrate by finding the top-left and bottom-right corners of the minimap
        tl = dll_helper.screenSearch(MM_TL_BMP, x1, y1, x2, y2)
        if tl:
            br = dll_helper.screenSearch(MM_BR_BMP,  x1, y1, x2, y2)

        if tl == None or br == None:
            now = time.time()
            if self.lost_minimap_time == 0:
                self.lost_minimap_time = now
            self.on_error(CaptureException(
                CaptureExceptionType.LOST_MINI_MAP, now - self.lost_minimap_time))
            return False

        self.lost_minimap_time = 0
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

    def locatePlayer(self, frame):
        frame = self.camera.get_latest_frame()
        if frame is None:
            return
        
        top = self.window['top']
        left = self.window['left']
        width = self.window['width']
        height = self.window['height']
        self.frame = frame[top:top+height, left:left+width]
        self.on_next(self.frame)
        
        # Crop the frame to only show the minimap
        minimap = self.frame[self.mm_tl[1]:self.mm_br[1], self.mm_tl[0]:self.mm_br[0]]
        if self.minimap_sample is None:
            self.minimap_sample = minimap
        self.minimap = minimap

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
            bot_status.player_pos = player[0]
            self.lost_player_time = 0
            self.on_next(player[0])
        else:
            now = time.time()
            if self.lost_player_time == 0:
                self.lost_player_time = now
            self.on_error(CaptureException(
                CaptureExceptionType.LOST_PLAYER, now - self.lost_player_time))

capture = Capture()

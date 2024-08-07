import win32gui
import win32con
import win32api
import win32clipboard as wc
import time
from io import BytesIO
import threading
from src.common import bot_status, utils
from mss import mss
import numpy as np
import cv2
from src.common.hid import hid
from src.modules.capture import capture
from src.common.image_template import WECHAT_CALL_TEMPLATE, WECHAT_CALL_TEMPLATE_2X
from src.chat_bot.chat_bot_entity import ChatBotEntity, ChatBotCommand

# info
WECHAT_BOT_COMMAND_INFO = 'i'
# begin
WECHAT_BOT_COMMAND_START = 'b'
# pause
WECHAT_BOT_COMMAND_PAUSE = 'p'
# screenshot
WECHAT_BOT_COMMAND_SCREENSHOT_MAPLE = 'sm'
# screenshot window
WECHAT_BOT_COMMAND_SCREENSHOT = 'ss'
# say
WECHAT_BOT_COMMAND_SAY = 's'
# tp
WECHAT_BOT_COMMAND_TP = 'tp'
# click
WECHAT_BOT_COMMAND_CLICK = 'c'
# change channel
WECHAT_BOT_COMMAND_CHANGE_CHANNEL = 'cc'
# test
WECHAT_BOT_COMMAND_TEST = 'test'


class WechatBot:

    def __init__(self, name, command_handler):
        self.name = name
        self.command_handler = command_handler
        self.hwnd = win32gui.FindWindow(None, name)
        self.last_msg = None
        self.window = {
            'left': 0,
            'top': 0,
            'width': 500,
            'height': 500
        }

        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def run(self):
        """Starts this WechatBot's thread."""
        print('\n[~] Started WechatBot')
        self.thread.start()

    def _main(self):

        if not self.hwnd:
            return
        x1, y1, x2, y2 = win32gui.GetWindowRect(self.hwnd)  # 获取当前窗口大小
        self.window['left'] = x1
        self.window['top'] = y1
        self.window['width'] = x2 - x1
        self.window['height'] = y2 - y1

        while True:
            msg = self.getNewMsg()
            if msg:
                self.handleMsg(msg)
            else:
                self.last_msg = None
            # hid.key_up('ctrl')
            time.sleep(0.5)

    def getNewMsg(self):
        if bot_status.rune_solving:
            return
        image = self.shot_new_msg()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        if np.count_nonzero(gray == 245) / height / width > 0.8:
            return

        lParam = win32api.MAKELONG(90, 460)
        win32gui.SendMessage(
            self.hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, lParam)
        win32gui.SendMessage(
            self.hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, lParam)

        return self.copy()

    def handleMsg(self, msg: str):
        if msg and msg != self.last_msg:
            self.last_msg = msg
            print(f'[wechat] {msg}')

            if msg == WECHAT_BOT_COMMAND_INFO:
                self.info_command()
            elif msg == WECHAT_BOT_COMMAND_START:
                self.start_command()
            elif msg == WECHAT_BOT_COMMAND_PAUSE:
                self.pause_command()
            elif msg == WECHAT_BOT_COMMAND_SCREENSHOT_MAPLE:
                self.screenshot_command(False)
            elif msg == WECHAT_BOT_COMMAND_SCREENSHOT:
                self.screenshot_command(True)
            elif msg == WECHAT_BOT_COMMAND_TP:
                self.tp_command()
            elif msg == WECHAT_BOT_COMMAND_CHANGE_CHANNEL:
                self.change_channel()
            elif msg.startswith(WECHAT_BOT_COMMAND_SAY):
                self.say_command(msg=msg)
            elif msg.startswith(WECHAT_BOT_COMMAND_CLICK):
                self.click_command(msg=msg)
            elif msg.startswith(WECHAT_BOT_COMMAND_TEST):
                self.test_command(msg=msg)
            else:
                self.send_text('unknow')

    def info_command(self):
        message, _ = self.command_handler(ChatBotCommand.INFO, )
        self.send_text(message)

    def start_command(self):
        message, _ = self.command_handler(ChatBotCommand.START, )
        self.send_text(message)

    def pause_command(self):
        message, _ = self.command_handler(ChatBotCommand.PAUSE, )
        self.send_text(message)

    def screenshot_command(self, full):
        _, image_path = self.command_handler(ChatBotCommand.PRINTSCREEN if full else ChatBotCommand.SCREENSHOT, )
        self.send_image(imagePath=image_path)

    def say_command(self, msg: str):
        list = msg.split(' ')
        if len(list) > 1:
            message, image_path = self.command_handler(ChatBotCommand.SAY, str(list[1]))
            self.send_message(message, imagePath=image_path)

    def click_command(self, msg: str):
        list = msg.split(' ')
        message, _ = self.command_handler(ChatBotCommand.CLICK, str(list[1]))
        self.send_message(message, capture.frame)
        
    def tp_command(self):
        message, image_path = self.command_handler(ChatBotCommand.TP, )
        self.send_message(message, imagePath=image_path)
        
    def change_channel(self):
        message, image_path = self.command_handler(ChatBotCommand.CHANGE_CHANNEL, )
        self.send_message(message, imagePath=image_path)
    
    def test_command(self, msg: str):
        list = msg.split(' ')
        message, image_path = self.command_handler(ChatBotCommand.TEST, int(list[1]))
        self.send_message(message, imagePath=image_path)
    
    def click(self, x, y):
        lParam = win32api.MAKELONG(x, y)
        win32gui.SendMessage(
            self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, None, lParam)

    def copy(self):
        try:
            wc.OpenClipboard()
            wc.EmptyClipboard()
            wc.CloseClipboard()
        except Exception as e:
            pass       

        hid.key_down('ctrl')
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, 0x43, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, 0x43, 0)
        hid.key_up('ctrl')

        try:
            wc.OpenClipboard()
            data = wc.GetClipboardData(win32con.CF_UNICODETEXT)
            wc.CloseClipboard()
        except Exception as e:
            data = None

        return data

    def paste(self):
        hid.key_down('ctrl')
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, 86, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, 86, 0)
        hid.key_up('ctrl')

    def send_text(self, text):
        if not hid:
            return

        try:
            wc.OpenClipboard()
            wc.EmptyClipboard()
            wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
            wc.CloseClipboard()
        except Exception as e:
            print(e)

        self.click(40, 550)
        self.paste()
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN,
                             win32con.VK_RETURN, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP,
                             win32con.VK_RETURN, 0)

    def send_image(self, image=None, imagePath=None):
        if not hid:
            return
        if image is None and imagePath is None:
            return
        if imagePath:
            image = cv2.imread(imagePath)
        image = utils.cvt2Plt(image)
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        try:
            wc.OpenClipboard()
            wc.EmptyClipboard()
            wc.SetClipboardData(win32con.CF_DIB, data)
            wc.CloseClipboard()
        except Exception as e:
            print(e) 

        self.click(40, 550)
        self.paste()
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN,
                             win32con.VK_RETURN, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP,
                             win32con.VK_RETURN, 0)

    def send_message(self, text=None, image=None, imagePath=None):
        while bot_status.rune_solving:
            time.sleep(0.2)
        if text:
            self.send_text(text)

        if image is not None:
            self.send_image(image=image)
        elif imagePath is not None:
            self.send_image(imagePath=imagePath)

    def voice_call(self):
        frame = utils.window_capture(self.hwnd)
        if frame is None:
            return
        location = utils.multi_match(
            frame, WECHAT_CALL_TEMPLATE, threshold=0.9)
        if not location:
            location = utils.multi_match(
                frame, WECHAT_CALL_TEMPLATE_2X, threshold=0.9)
        if location:
            self.click(location[0][0], location[0][1])

    def video_call(self):
        self.click(510, 530)

    def shot_new_msg(self):
        frame = utils.window_capture(self.hwnd)
        if frame is not None:
            frame = frame[430:500, 0:70]
        # cv2.imshow("", frame)
        # cv2.waitKey(0)
        return frame


# if __name__ == "__main__":
#     chat_bot = WechatBot("yep")
#     chat_bot.run()
    # image = utily.window_capture(bot.hwnd)
    # image = bot.cvt2Plt(image)
    # image = Image.open('screenshot/Maple_230713_144732.png')
    # bot.send_message('title', image=image)
    # msg = bot.getNewMsg()
    # print(msg)


import win32con
import win32clipboard as wc
import time
from random import random
from src.common import utils, bot_status
from src.common.hid import hid
from src.common.image_template import *
from src.modules.capture import capture
from src.command.commands import Keybindings
from src.modules.chat_bot import chat_bot
import threading


class ActionSimulator:

    @staticmethod
    def setText(text):
        wc.OpenClipboard()
        wc.EmptyClipboard()
        wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
        wc.CloseClipboard()

    @staticmethod
    def say(text):
        ActionSimulator.setText(text)
        ActionSimulator.click_key('enter', 0.3)
        ActionSimulator.press_key("ctrl", 0.05)
        ActionSimulator.click_key("v", 0.05)
        ActionSimulator.release_key("ctrl", 0.3)
        ActionSimulator.click_key('enter', 0.3)
        ActionSimulator.click_key('enter', 0.05)

    @staticmethod
    def say_to_all(text):
        last_status = bot_status.enabled
        bot_status.enabled = False
        time.sleep(1)
        ActionSimulator.say(text)
        if last_status:
            bot_status.enabled = True

    @staticmethod
    def go_home():
        for i in range(0, 6):
            bot_status.enabled = False
        ActionSimulator.click_key('H', 0.5)
        ActionSimulator.click_key('H', 5)

    @staticmethod
    def stop_game():
        bot_status.enabled = False

        ActionSimulator.press_key('alt', 0.5)
        ActionSimulator.click_key('f4', 0.5)
        ActionSimulator.release_key('alt', 0.5)
        ActionSimulator.click_key('enter', 10)
        hid.consumer_sleep()

    @staticmethod
    def jump_down():
        bot_status.enabled = False
        ActionSimulator.press_key('left', 0.1)
        ActionSimulator.click_key('s', 0.5)
        ActionSimulator.click_key('s', 0.5)
        ActionSimulator.release_key('left', 0.5)
        bot_status.enabled = True

    @staticmethod
    def potion_buff():
        hid.key_press('0')
        time.sleep(0.5)
        hid.key_press('-')

    @staticmethod
    def click_key(key, delay=0):
        hid.key_press(key)
        time.sleep(delay * (1 + 0.2 * random()))

    @staticmethod
    def press_key(key, delay=0.05):
        hid.key_down(key)
        time.sleep(delay * (1 + 0.2 * random()))

    @staticmethod
    def release_key(key, delay=0.05):
        hid.key_up(key)
        time.sleep(delay * (1 + 0.2 * random()))
        
    @staticmethod
    def mouse_left_click(position=None, delay=0.05):
        if position:
            hid.mouse_abs_move(position[0], position[1])
            time.sleep(0.5)

        hid.mouse_left_click()
        time.sleep(delay * (1 + 0.2 * random()))
        
    @staticmethod
    def cancel_rune_buff():
        for _ in range(5):
            rune_buff = utils.multi_match(
                capture.frame[:200, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
            if len(rune_buff) <= 2:
                break
            
            rune_buff_pos = min(rune_buff, key=lambda p: p[0])
            x = round(rune_buff_pos[0] + capture.window['left']) + 10
            y = round(rune_buff_pos[1] + capture.window['top']) + 10
            hid.mouse_abs_move(x, y)
            time.sleep(0.06)
            hid.mouse_right_down()
            time.sleep(0.2)
            hid.mouse_right_up()
            time.sleep(0.5)

    @staticmethod
    def open_boss_box():
        for _ in range(35):
            hid.key_press('4')
            time.sleep(1)

    @staticmethod
    def go_to_msroom(num: int):
        ActionSimulator.click_key('f8')

        ActionSimulator.change_channel(num=num, enable=False)

    @staticmethod
    def change_channel(num: int = 0, enable=True):
        bot_status.enabled = False
        bot_status.change_channel = True
        bot_status.rune_pos = None
        bot_status.rune_closest_pos = None
        threading.Timer(5, ActionSimulator._change_channel, (num, enable, )).start()
        chat_bot.send_message('changing channel...')

    @staticmethod
    def _change_channel(num: int = 0, enable=True) -> None:

        ActionSimulator.click_key(Keybindings.Change_Channel)

        if num > 0:
            item_width = 50
            item_height = 40
            channel_1 = (0, 0)

            row = (num - 1) // 10
            col = (num - 1) % 10

            x = channel_1[0] + col * item_width
            y = channel_1[1] + row * item_height
            hid.mouse_abs_move(x, y)
            hid.mouse_left_click()
        else:
            ActionSimulator.click_key('down')
            ActionSimulator.click_key('right')
            ActionSimulator.click_key('enter')
        time.sleep(1)

        frame = capture.frame
        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 220) // 2
        ok_btn = utils.multi_match(
            frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)
        if ok_btn:
            ActionSimulator.click_key('esc')
            time.sleep(1)
            ActionSimulator._change_channel(num, enable)
            return

        delay = 0
        while not bot_status.lost_minimap:
            print("changging channel")
            delay += 0.1
            if delay > 5:
                ActionSimulator._change_channel()
                return
            time.sleep(0.1)

        while bot_status.lost_minimap:
            print("cc: lost mimimap")
            time.sleep(0.1)

        if not enable:
            return

        chat_bot.send_message('channel changed', capture.frame)
        bot_status.enabled = True
        time.sleep(3)
        others = False
        for i in range(5):
            if bot_status.stage_fright:
                others = True
                break
            time.sleep(1)

        if others:
            ActionSimulator.change_channel()
        else:
            bot_status.change_channel = False

    @staticmethod
    def auto_login(channel=40):
        bot_status.enabled = False
        
        ActionSimulator.click_key('esc', delay=1)
        ActionSimulator.mouse_left_click((960, 186), delay=1)
        channel_pos = ActionSimulator.get_channel_pos(channel)
        ActionSimulator.mouse_left_click(channel_pos, delay=0.5)
        ActionSimulator.click_key('enter', delay=0.08)
        ActionSimulator.click_key('enter', delay=0.5)

        bot_status.enabled = True

    @staticmethod
    def get_channel_pos(channel):
        width = 385
        height = 244
        column = 5
        row = 8 
        cell_width = width // column
        cell_height = height // row
        
        channel_row = (channel - 1) // column
        channel_column = (channel - 1) % column
        return channel_column * cell_width + cell_width // 2, channel_row * cell_height + cell_height // 2
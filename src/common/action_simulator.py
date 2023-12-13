
import win32con
import win32clipboard as wc
import time
from random import random
from src.common import utils, bot_status
from src.common.hid import hid
from src.common.image_template import *
from src.modules.capture import capture
from src.command.commands import Keybindings, detect_mobs
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
    def change_channel(num: int = 0, enable=True, instance = True):
        bot_status.enabled = False
        bot_status.change_channel = True
        bot_status.rune_pos = None
        bot_status.rune_closest_pos = None
        threading.Timer(5, ActionSimulator._change_channel, (num, enable, instance)).start()
        chat_bot.send_message('changing channel...')

    @staticmethod
    def _change_channel(num: int = 0, enable=True, instance = True) -> None:

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
        time.sleep(3)
        map_available = chenck_map_available(instance=instance)
        
        if map_available:
            bot_status.enabled = True
            bot_status.change_channel = False
        else:
            ActionSimulator.change_channel()
            
    @staticmethod
    def auto_login(channel=33):
        chat_bot.send_message(f'auto login:{channel}')

        if channel not in range(1, 41):
            chat_bot.send_message(f'auto login failed: wrong channel:{channel}')
            return
        bot_status.enabled = False
        
        matches = utils.multi_match(capture.frame, BUTTON_ERROR_OK_TEMPLATE, 0.9)
        if matches:
            ActionSimulator.click_key('esc', delay=1)
        ActionSimulator.mouse_left_click((capture.window['left'] + 968, capture.window['top'] + 192), delay=2)
        channel_pos = get_channel_pos(channel)
        ActionSimulator.mouse_left_click(channel_pos, delay=1)
        hid.mouse_left_click()
        
        while len(utils.multi_match(capture.frame, END_PLAY_TEMPLATE, 0.98)) == 0:
            time.sleep(0.1)
            
        time.sleep(2)

        while utils.multi_match(capture.frame, END_PLAY_TEMPLATE, 0.98):
            ActionSimulator.click_key('enter', delay=2)

        while bot_status.lost_minimap:
            print("cc: lost mimimap")
            time.sleep(0.1)

        time.sleep(1)
        map_available = chenck_map_available()
        if map_available:
            bot_status.enabled = True
            chat_bot.send_message(f'auto login:{channel}. success')
        else:
            ActionSimulator.change_channel()
        
    @staticmethod
    def run_maplestory():
        capture.find_window()
        hwnd = capture.hwnd
        if hwnd != 0:
            return
        matches = utils.multi_match(capture.camera.get_latest_frame(), BUTTON_ERROR_OK_TEMPLATE, 0.9)
        if matches:
            ActionSimulator.mouse_left_click(matches[0], 2)
        else:
            return
            
        play_matches = utils.multi_match(capture.camera.get_latest_frame(), BUTTON_ERROR_OK_TEMPLATE, 0.9)
        if play_matches:
            ActionSimulator.mouse_left_click(play_matches, 2)
            

        

    

def get_full_pos(pos):
    return pos[0] + capture.window['left'], pos[1] + capture.window['top']

def get_channel_pos(channel):
    x = 334 + capture.window['left']
    y = 290 + capture.window['top']
    width = 360
    height = 244
    column = 5
    row = 8 
    cell_width = width // column
    cell_height = height // row
    
    channel_row = (channel - 1) // column
    channel_column = (channel - 1) % column
    return x + channel_column * cell_width + cell_width // 2, y + channel_row * cell_height + cell_height // 2

def chenck_map_available(instance=True):
    if instance:
        start_time = time.time()
        while time.time() - start_time <= 5:
            if detect_mobs():
                return True
            time.sleep(0.1)
        return False
    else:
        for i in range(5):
            if bot_status.stage_fright:
                return False
            time.sleep(1)
        return True

import win32con
import win32clipboard as wc
import time
import threading
from random import random

from src.common import utils, bot_status, bot_settings
from src.common.bot_helper import *
from src.common.hid import hid
from src.common.constants import *
from src.common.image_template import *
from src.modules.capture import capture
from src.modules.chat_bot import chat_bot


############################
#      Common Actions      #
############################

def click_key(key, delay=0):
    hid.key_press(key)
    time.sleep(delay * (1 + 0.2 * random()))


def press_key(key, delay=0.05):
    hid.key_down(key)
    time.sleep(delay * (1 + 0.2 * random()))


def release_key(key, delay=0.05):
    hid.key_up(key)
    time.sleep(delay * (1 + 0.2 * random()))


def mouse_move(template, rect: Rect = None, ranges=None):
    frame = capture.frame
    if frame is None:
        return False
    if rect is not None:
        frame = frame[rect.y:rect.y+rect.height, rect.x:rect.x+rect.width]
    if ranges is not None:
        frame = utils.filter_color(frame, ranges)
    match = utils.multi_match(frame, template, threshold=0.9)
    if match:
        x, y = match[0]
        if rect is not None:
            x += rect.x
            y += rect.y
        hid.mouse_abs_move(*get_full_pos((x, y)))
        time.sleep(0.2 + 0.1 * random())
        return True
    return False

def mouse_move_relative(x, y):
    hid.mouse_relative_move(x, y)
    time.sleep(0.3 + 0.2 * random())

def mouse_left_click(position=None, delay=0.05):
    if position:
        hid.mouse_abs_move(position[0], position[1])
        time.sleep(0.3)

    hid.mouse_left_click()
    time.sleep(delay * (1 + random()))


def mouse_double_click(position=None, delay=0.05):
    if position:
        hid.mouse_abs_move(position[0], position[1])
        time.sleep(0.3)

    hid.mouse_left_click()
    time.sleep(delay * (1 + random()))
    hid.mouse_left_click()
    time.sleep(delay * (1 + random()))


def setClipboard(text: str):
    wc.OpenClipboard()
    wc.EmptyClipboard()
    wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
    wc.CloseClipboard()


############################
#      Common Actions      #
############################

def say(text: str):
    setClipboard(text)
    click_key('enter', 0.3)
    press_key("ctrl", 0.05)
    click_key("v", 0.05)
    release_key("ctrl", 0.3)
    click_key('enter', 0.3)
    click_key('enter', 0.05)


def say_to_all(text):
    last_status = bot_status.enabled
    bot_status.enabled = False
    time.sleep(1)
    say(text)
    if last_status:
        bot_status.enabled = True


def jump_down():
    bot_status.enabled = False
    press_key('left', 0.1)
    click_key('s', 0.5)
    click_key('s', 0.5)
    release_key('left', 0.5)
    bot_status.enabled = True


def climb_rope(isUP=True):
    step = 0
    key = 'up' if isUP else 'down'
    press_key(key)
    time.sleep(0.1)
    while not shared_map.on_the_platform(bot_status.player_pos):
        time.sleep(0.1)
        step += 1
        if step > 50:
            break
    release_key(key)


def teleport_to_map(map_name: str):
    bot_status.enabled = False
    if not mouse_move(TELEPORT_STONE_TEMPLATE):
        cash_tab = utils.multi_match(capture.frame, ITEM_CASH_TAB_TEMPLATE)
        if not cash_tab:
            click_key(bot_settings.SystemKeybindings.ITEM, 0.5)
            teleport_to_map(map_name)
        else:
            mouse_move(ITEM_CASH_TAB_TEMPLATE)
            mouse_left_click(delay=1)
            teleport_to_map(map_name)
    else:
        mouse_double_click()
        map_template_path = f'assets/exceptions/{map_name}_stone_template.png'
        map_template = cv2.imread(map_template_path, 0)
        if not mouse_move(map_template):
            print("[error]cant fine stored map")
            return
        mouse_left_click()
        if not mouse_move(TELEPORT_STONE_MOVE_TEMPLATE):
            print("[error]cant fine move button")
            return
        mouse_left_click()
        click_key('enter')
        wait_until_map_changed()
        bot_status.enabled = True


def go_home():
    for i in range(0, 6):
        bot_status.enabled = False
    click_key('H', 0.5)
    click_key('H', 5)


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


def open_boss_box():
    pass


def change_channel(num: int = 0, enable=True, instance=True):
    bot_status.enabled = False
    bot_status.change_channel = True
    bot_status.rune_pos = None
    bot_status.rune_closest_pos = None
    threading.Timer(5, _change_channel, (num, enable, instance)).start()
    chat_bot.send_message('changing channel...')


def _change_channel(num: int = 0, enable=True, instance=True) -> None:

    click_key(bot_settings.SystemKeybindings.Change_Channel)

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
        click_key('down')
        click_key('right')
        click_key('enter')
    time.sleep(1)

    frame = capture.frame
    x = (frame.shape[1] - 260) // 2
    y = (frame.shape[0] - 220) // 2
    ok_btn = utils.multi_match(
        frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)
    if ok_btn:
        click_key('esc')
        time.sleep(1)
        _change_channel(num, enable)
        return

    wait_until_map_changed()

    if not enable:
        return

    chat_bot.send_message('channel changed', capture.frame)
    time.sleep(2)

    if chenck_map_available(instance=instance):
        bot_status.enabled = True
        bot_status.change_channel = False
    else:
        change_channel()


def auto_login(channel=33):
    chat_bot.send_message(f'try auto login:{channel}')

    if channel not in range(1, 41):
        chat_bot.send_message(f'auto login failed: wrong channel:{channel}')
        return
    bot_status.enabled = False

    matches = utils.multi_match(capture.frame, BUTTON_ERROR_OK_TEMPLATE, 0.9)
    if matches:
        click_key('esc', delay=1)
    mouse_left_click(
        (capture.window['left'] + 968, capture.window['top'] + 192), delay=2)
    channel_pos = get_channel_pos(channel)
    mouse_left_click(channel_pos, delay=1)
    hid.mouse_left_click()

    while len(utils.multi_match(capture.frame, END_PLAY_TEMPLATE, 0.98)) == 0:
        time.sleep(0.1)

    time.sleep(2)

    while utils.multi_match(capture.frame, END_PLAY_TEMPLATE, 0.98):
        click_key('enter', delay=2)

    while bot_status.lost_minimap:
        print("cc: lost mimimap")
        time.sleep(0.1)

    time.sleep(1)
    map_available = chenck_map_available()
    if map_available:
        bot_status.enabled = True
        chat_bot.send_message(f'auto login:{channel}. success')
    else:
        change_channel()

def relogin(channel=33):
    chat_bot.send_message(f'Relogin:{channel}')

    bot_status.enabled = False

    hid.key_press('esc')
    time.sleep(0.5)
    hid.key_press('up')
    time.sleep(0.5)
    hid.key_press('enter')
    time.sleep(0.2)
    hid.key_press('enter')
    time.sleep(2)
    while len(utils.multi_match(capture.frame, BUTTON_CHANGE_REGION_TEMPLATE, threshold=0.95)) == 0:
        time.sleep(0.1)
        print("wait regoin")
    time.sleep(2)
    auto_login(channel)

def run_maplestory():
    capture.find_window()
    hwnd = capture.hwnd
    if hwnd != 0:
        return
    matches = utils.multi_match(
        capture.camera.get_latest_frame(), BUTTON_ERROR_OK_TEMPLATE, 0.9)
    if matches:
        mouse_left_click(matches[0], 2)
    else:
        return

    play_matches = utils.multi_match(
        capture.camera.get_latest_frame(), BUTTON_ERROR_OK_TEMPLATE, 0.9)
    if play_matches:
        mouse_left_click(play_matches, 2)


def stop_game():
    bot_status.enabled = False

    press_key('alt', 0.5)
    click_key('f4', 0.5)
    release_key('alt', 0.5)
    click_key('enter', 10)
    hid.consumer_sleep()

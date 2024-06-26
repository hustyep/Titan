
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
from src.chat_bot.chat_bot import chat_bot


############################
#      Common Actions      #
############################

@bot_status.run_if_enabled
def click_key(key, delay=0.05):
    hid.key_press(key)
    time.sleep(delay * (1 + 0.2 * random()))


@bot_status.run_if_enabled
def press_key(key, delay=0.05):
    hid.key_down(key)
    time.sleep(delay * (1 + 0.2 * random()))


@bot_status.run_if_enabled
def release_key(key, delay=0.05):
    hid.key_up(key)
    time.sleep(delay * (1 + 0.2 * random()))


@bot_status.run_if_enabled
def mouse_move(template, rect: Rect | None = None, ranges=None, threshold=0.9, debug=False):
    frame = capture.frame
    if frame is None:
        return False
    if rect is not None:
        frame = frame[rect.y:rect.y+rect.height, rect.x:rect.x+rect.width]
    if ranges is not None:
        frame = utils.filter_color(frame, ranges)
    match = utils.multi_match(frame, template, threshold, debug=debug)
    if match:
        x, y = match[0]
        if rect is not None:
            x += rect.x
            y += rect.y
        hid.mouse_abs_move(*get_full_pos((x, y)))
        time.sleep(0.2 + 0.1 * random())
        return True
    return False


@bot_status.run_if_enabled
def mouse_move_relative(x, y):
    hid.mouse_relative_move(x, y)
    time.sleep(0.3 + 0.2 * random())


@bot_status.run_if_enabled
def mouse_left_click(position=None, delay=0.05):
    if position:
        hid.mouse_abs_move(position[0], position[1])
        time.sleep(0.3)

    hid.mouse_left_click()
    time.sleep(delay * (1 + random()))


@bot_status.run_if_enabled
def mouse_double_click(position=None, delay=0.05):
    if position:
        hid.mouse_abs_move(position[0], position[1])
        time.sleep(0.3)

    hid.mouse_left_click()
    time.sleep(0.06)
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

def __say(text: str):
    setClipboard(str(text))
    click_key('enter', 0.3)
    press_key("ctrl", 0.05)
    click_key("v", 0.05)
    release_key("ctrl", 0.3)
    click_key('enter', 0.3)
    click_key('enter', 0.05)


@bot_status.run_if_enabled
def say_to_all(text):
    bot_status.acting = True
    time.sleep(1)
    __say(text)
    time.sleep(0.5)
    bot_status.acting = False


def jump_down():
    bot_status.acting = True
    press_key('left', 0.1)
    click_key('s', 0.5)
    click_key('s', 0.5)
    release_key('left', 0.5)
    bot_status.acting = False


@bot_status.run_if_enabled
def climb_rope(isUP=True):
    bot_status.acting = True
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
    bot_status.acting = False


@bot_status.run_if_enabled
def open_teleport_stone(retry_count=0) -> bool:
    def is_opend():
        match = utils.multi_match(
            capture.frame, TELEPORT_STONE_LIST_ICON_TEMPLATE)
        return len(match) > 0

    if is_opend():
        return True

    if retry_count >= 5:
        return False

    if not mouse_move(TELEPORT_STONE_TEMPLATE):
        if mouse_move(ITEM_CASH_TAB_TEMPLATE):
            mouse_left_click(delay=0.5)
            stone_match = utils.multi_match(
                capture.frame, TELEPORT_STONE_TEMPLATE)
            if len(stone_match) > 0:
                return open_teleport_stone(retry_count+1)
            else:
                print("[error]cant find teleport stone")
                return False
        else:
            click_key(bot_settings.SystemKeybindings.ITEM, 0.5)
            mouse_move_relative(0, 20)
            return open_teleport_stone(retry_count+1)

    else:
        mouse_double_click(delay=0.1)
        if not is_opend():
            click_key('i', delay=0.1)
            mouse_move_relative(0, 20)
            open_teleport_stone(retry_count+1)
        return True


@bot_status.run_if_enabled
def close_teleport_stone():
    mouse_move(TELEPORT_STONE_CLOSE_TEMPLATE,
               Rect(700, 200, 100, 30), threshold=0.8)
    mouse_left_click()


@bot_status.run_if_enabled
def teleport_to_map(map_name: str, retried_count=0, max_retry_count=5) -> bool:
    if retried_count >= max_retry_count:
        bot_status.acting = False
        return False

    bot_status.acting = True
    bot_status.prepared = False
    if open_teleport_stone():
        # click_key('i')
        mouse_move_relative(300, 0)
        time.sleep(1)
        map_template_path = f'assets/teleport/{map_name}.png'
        map_template = cv2.imread(map_template_path, 0)
        if not mouse_move(map_template, debug=False):
            print("[error]cant find stored map")
            teleport_random_town()
            bot_status.acting = False
            return False
        mouse_left_click(delay=0.3)
        if not mouse_move(TELEPORT_STONE_MOVE_TEMPLATE):
            print("[error]cant find move button")
            close_teleport_stone()
            bot_status.acting = False
            return False
        mouse_left_click(delay=0.3)
        frame = capture.frame
        if frame is None:
            return False
        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 100) // 2
        frame = frame[y:y+100, x:x+260]
        if utils.match_count(capture.frame, BUTTON_CANCEL_TEMPLATE):
            click_key('enter', delay=0.1)
            result = wait_until_map_changed()
            bot_status.acting = False
            return result
        elif utils.match_count(capture.frame, TELEPORT_CURRENT_MAP_ERROR_TEMPLATE):
            click_key('esc', delay=0.1)
            bot_status.acting = False
            return True
        else:
            click_key('esc', delay=0.1)
            click_key('esc', delay=0.1)
            return teleport_to_map(map_name, retried_count+1)
    else:
        print("[error]cant open teleport stone")
        bot_status.acting = False
        return False


@bot_status.run_if_enabled
def teleport_random_town():
    bot_status.acting = True
    bot_status.prepared = False
    if open_teleport_stone():
        if not mouse_move(TELEPORT_STONE_SHOW_TOWNS_TEMPLATE):
            print("[error]cant fined TELEPORT_STONE_SHOW_TOWNS_TEMPLATE")
            close_teleport_stone()
            go_home()
            bot_status.acting = False
            return
        mouse_left_click()
        press_key("down")
        time.sleep(0.3)
        release_key('down')
        time.sleep(0.1)
        click_key('enter', delay=0.5)
        if not mouse_move(TELEPORT_STONE_MOVE_TEMPLATE):
            print("[error]cant find move button")
            close_teleport_stone()
            go_home()
            bot_status.acting = False
            return
        mouse_left_click(delay=0.3)
        frame = capture.frame
        if not frame:
            return
        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 100) // 2
        frame = frame[y:y+100, x:x+260]
        cancel_match = utils.multi_match(frame, BUTTON_CANCEL_TEMPLATE)
        if len(cancel_match) > 0:
            click_key('enter')
            wait_until_map_changed()
        else:
            click_key('esc', delay=0.1)
            click_key('esc')
            teleport_random_town()
    else:
        print("[error]cant open teleport stone")
        go_home()
    bot_status.acting = False


@bot_status.run_if_enabled
def change_channel(num: int = 0, instance=True):
    chat_bot.send_message('changing channel...')
    bot_status.acting = True
    time.sleep(2)
    _change_channel(num, instance)
    bot_status.acting = False


@bot_status.run_if_enabled
def _change_channel(num: int = 0, instance=True) -> None:
    bot_status.acting = True
    bot_status.prepared = False
    bot_status.stage_fright = False
    bot_status.rune_pos = None
    bot_status.rune_closest_pos = None
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
    if frame is None:
        return
    x = (frame.shape[1] - 260) // 2
    y = (frame.shape[0] - 220) // 2
    ok_btn = utils.multi_match(
        frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)
    if ok_btn:
        click_key('esc')
        time.sleep(1)
        _change_channel(num, instance)
        return

    wait_until_map_changed()

    if not bot_status.enabled:
        return

    chat_bot.send_message('channel changed', capture.frame)
    time.sleep(2)

    if chenck_map_available(instance=instance):
        bot_status.acting = False
    else:
        _change_channel(num, instance)


@bot_status.run_if_enabled
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


@bot_status.run_if_enabled
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


@bot_status.run_if_enabled
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


@bot_status.run_if_enabled
def go_home():
    bot_status.enabled = False
    for i in range(0, 6):
        bot_status.enabled = False
    click_key('H', 0.5)
    click_key('H', 5)


# @bot_status.run_if_enabled
# def cancel_rune_buff():
#     for _ in range(5):
#         rune_buff = utils.multi_match(
#             capture.frame[:200, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
#         if len(rune_buff) <= 2:
#             break

#         rune_buff_pos = min(rune_buff, key=lambda p: p[0])
#         x = round(rune_buff_pos[0] + capture.window['left']) + 10
#         y = round(rune_buff_pos[1] + capture.window['top']) + 10
#         hid.mouse_abs_move(x, y)
#         time.sleep(0.06)
#         hid.mouse_right_down()
#         time.sleep(0.2)
#         hid.mouse_right_up()
#         time.sleep(0.5)


# def open_boss_box():
#     pass


# @bot_status.run_if_enabled
# def go_ardentmill(key):
#     click_key(key)
#     time.sleep(5)

#     if not mouse_move(Go_Ardentmill_TEMPLATE):
#         click_key(bot_settings.SystemKeybindings.Go_Ardentmill, delay=0.5)
#     if not mouse_move(Go_Ardentmill_TEMPLATE):
#         print("cool down")
#         hid.key_press('esc')
#         time.sleep(1)
#         bot_status.enabled = True
#         return
#     mouse_left_click()

#     frame = capture.frame
#     x = (frame.shape[1] - 260) // 2
#     y = (frame.shape[0] - 220) // 2
#     ok_btn = utils.multi_match(
#         frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)
#     cancel_btn = utils.multi_match(
#         frame, BUTTON_CANCEL_TEMPLATE, threshold=0.9, debug=False)
#     if cancel_btn:
#         print("ok")
#         hid.key_press("enter")
#         time.sleep(1)
#     else:
#         print("not ok")
#         hid.key_press('esc')
#         time.sleep(0.2)
#         return

#     wait_until_map_changed()
#     time.sleep(2)
#     hid.key_press('up')
#     time.sleep(0.5)
#     while (not bot_status.lost_minimap):
#         hid.key_press('up')
#         time.sleep(0.3)
#     while (bot_status.lost_minimap):
#         time.sleep(0.1)
#     time.sleep(2)
#     hid.key_press('esc')


def stop_game():
    bot_status.enabled = False

    press_key('alt', 0.5)
    click_key('f4', 0.5)
    release_key('alt', 0.5)
    click_key('enter', 10)
    hid.consumer_sleep()


@bot_status.run_if_enabled
def take_daily_quest():
    bot_status.acting = True
    mouse_move(QUEST_BUBBLE_TEMPLATE,
               Rect(0, 200, 100, 100),
               YELLOW_RANGES)
    mouse_left_click(delay=0.3)
    click_key('down')
    click_key(
        bot_settings.SystemKeybindings.INTERACT, delay=0.3)
    click_key('y', delay=0.3)
    click_key(
        bot_settings.SystemKeybindings.INTERACT, delay=0.3)
    bot_status.acting = False

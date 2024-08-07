import time
import os
import numpy as np

from src.common import utils, bot_status, bot_settings
from src.common.gui_setting import gui_setting
from src.common.constants import *
from src.common.image_template import *
from src.modules.capture import capture
from src.map.map import shared_map


def identify_role_name():
    name = utils.image_match_text(capture.name_frame, list(Name_Class_Map.keys()))
    return name


def detect_mobs_in_rect(
        rect: Rect,
        type: MobType = MobType.NORMAL,
        multy_match=False,
        debug=False):
    frame = capture.frame
    if frame is None:
        return []
    if rect is not None:
        crop = frame[rect.y:rect.y+rect.height, rect.x+rect.width]
    else:
        crop = frame
    return detect_mobs(crop, type, multy_match, debug)


def detect_mobs_around_anchor(
        anchor: tuple[int, int] | None = None,
        insets: AreaInsets | None = None,
        type: MobType = MobType.NORMAL,
        multy_match=False,
        debug=False):
    frame = capture.frame

    if frame is None:
        return []
    crop = frame
    if insets is not None:
        if anchor is None:
            anchor = convert_point_minimap_to_window(
                bot_status.player_pos)
        crop = frame[max(0, anchor[1]-insets.top):anchor[1]+insets.bottom,
                     max(0, anchor[0]-insets.left):anchor[0]+insets.right]
        # utils.show_image(crop)
    return detect_mobs(crop, type, multy_match, debug)


def detect_mobs(
        frame,
        type: MobType = MobType.NORMAL,
        multy_match=False,
        debug=False):
    if frame is None or shared_map.current_map is None:
        return []

    match (type):
        case (MobType.BOSS):
            mob_templates = shared_map.current_map.boss_templates
        case (MobType.ELITE):
            mob_templates = shared_map.current_map.elite_templates
        case (_):
            mob_templates = shared_map.current_map.mob_templates

    if len(mob_templates) == 0:
        if type == MobType.NORMAL:
            raise ValueError(f"Missing {type.value} template")
        else:
            return []

    mobs = []
    for mob_template in mob_templates:
        mobs_tmp = utils.multi_match(
            frame,
            mob_template,
            threshold=0.95 if type == MobType.NORMAL else 0.9,
            debug=debug)
        if len(mobs_tmp) > 0:
            for mob in mobs_tmp:
                mobs.append(mob)
                if not multy_match:
                    print(f"mobs count = {len(mobs)}")
                    return mobs
    return mobs


def pre_detect(direction):
    anchor = locate_player_fullscreen(accurate=True)
    insets = AreaInsets(top=150,
                        bottom=50,
                        left=-620 if direction == 'right' else 1000,
                        right=1000 if direction == 'right' else -620)
    matchs = []
    if gui_setting.detection.detect_elite:
        matchs = detect_mobs_around_anchor(
            insets=insets, anchor=anchor, type=MobType.ELITE)
    if not matchs and gui_setting.detection.detect_boss:
        matchs = detect_mobs_around_anchor(
            insets=insets, anchor=anchor, type=MobType.BOSS)
    return len(matchs) > 0


@bot_status.run_if_enabled
def sleep_while_move_y(interval=0.02, n=15):
    player_y = bot_status.player_pos.y
    count = 0
    while True:
        time.sleep(interval)
        if player_y == bot_status.player_pos.y:
            count += 1
        else:
            count = 0
            player_y = bot_status.player_pos.y
        if count == n:
            break


@bot_status.run_if_enabled
def sleep_in_the_air(interval=0.005, n=4, detect_rope=False):
    if shared_map.minimap_data is None or len(shared_map.minimap_data) == 0:
        sleep_while_move_y(interval, n)
        return
    count = 0
    step = 0
    last_y = bot_status.player_pos.y
    while True:
        pos = bot_status.player_pos
        if not shared_map.is_floor_point(pos):
            count = 0
        else:
            if pos.y != last_y:
                count = 0
            count += 1
        if count >= n:
            break
        last_y = pos.y
        step += 1
        if step >= 600:
            utils.log_event("sleep_in_the_air timeout")
            break
        elif detect_rope and step >= 250 and shared_map.on_the_rope(bot_status.player_pos):
            # 检测是否在绳子上
            break
        time.sleep(interval)


def wait_until_map_changed(timeout=7):
    start = time.time()
    while (not bot_status.lost_minimap):
        time.sleep(0.5)
        print("not lost_minimap")

        if time.time() - start > timeout:
            return False
    while (bot_status.lost_minimap):
        print("lost_minimap")
        time.sleep(0.5)
        if time.time() - start > timeout:
            print("change map timeout")
            return False
    print("map loaded")
    time.sleep(0.5)
    return True


def chenck_map_available(instance=True):
    if instance:
        start_time = time.time()
        while time.time() - start_time <= 3:
            if detect_mobs(capture.frame):
                return True
            time.sleep(0.1)
        return False
    else:
        for i in range(4):
            if bot_status.stage_fright:
                return False
            time.sleep(0.5)
        return True


def get_available_routines(command_name) -> list:
    routines = []
    folder = bot_settings.get_routines_dir(command_name)
    for root, ds, fs in os.walk(folder):
        for f in fs:
            if f.endswith(".csv"):
                routines.append(f[:-4])
    return routines


def identify_map_name(try_count=1):
    available_map_names = []
    for map in shared_map.available_maps:
        available_map_names.append(map.name)

    frame = capture.map_name_frame
    # utils.show_image(frame)
    for _ in range(0, try_count):
        result = utils.image_match_text(
            frame, available_map_names, 0.8, filter=[])
        if not result:
            time.sleep(0.3)
        else:
            return result


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


def convert_point_minimap_to_window(point: MapPoint):
    '''convent the minimap point to the window point'''
    assert(capture.minimap_frame is not None)
    window_width = capture.window_rect.width
    window_height = capture.window_rect.height

    mini_height, mini_width, _ = capture.minimap_frame.shape

    map_width = mini_width * MINIMAP_SCALE
    map_height = mini_height * MINIMAP_SCALE

    map_x = point.x * MINIMAP_SCALE
    map_y = point.y * MINIMAP_SCALE

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


# -> tuple | tuple[int, int]:
def locate_player_fullscreen(accurate=False):
    player_pos = convert_point_minimap_to_window(
        bot_status.player_pos)

    frame = capture.frame
    if accurate and frame:
        role_template = bot_settings.role.name_template  # type: ignore
        tl_x = player_pos[0]-50
        tl_y = player_pos[1]
        player_crop = frame[tl_y:tl_y+250, tl_x-150:tl_x+150]
        matchs = utils.multi_match(player_crop,
                                   role_template,
                                   threshold=0.9,
                                   debug=False)
        if matchs:
            player_pos = (matchs[0][0] - 150 + tl_x,
                          matchs[0][1] - 140 + tl_y)
    return player_pos


def rune_buff_match(frame):
    rune_buff = utils.multi_match(
        frame[:150, :], RUNE_BUFF_TEMPLATE[1:11, -15:-1], threshold=0.9)
    if len(rune_buff) == 0:
        rune_buff = utils.multi_match(
            frame[:150, :], RUNE_BUFF_GRAY_TEMPLATE, threshold=0.8)
    return rune_buff


def check_blind():
    gray = cv2.cvtColor(capture.frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    if not bot_status.lost_minimap and np.count_nonzero(gray < 15) / height / width > 0.7:
        return True
    else:
        return False
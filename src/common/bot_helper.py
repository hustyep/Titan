import time
import os

from src.common import utils, bot_status, bot_settings
from src.common.gui_setting import gui_setting
from src.common.constants import *
from src.common.image_template import *
from src.modules.capture import capture
from src.map.map import shared_map


def identify_role_name():
    name = utils.image_match_text(capture.name_frame, Name_Class_Map.keys())
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
        anchor: tuple[int, int] = None,
        insets: AreaInsets = None,
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
    if frame is None:
        return []

    match (type):
        case (MobType.BOSS):
            mob_templates = shared_map.boss_templates
        case (MobType.ELITE):
            mob_templates = shared_map.elite_templates
        case (_):
            mob_templates = shared_map.mob_templates

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
        matchs = detect_mobs(insets=insets, anchor=anchor, type=MobType.ELITE)
    if not matchs and gui_setting.detection.detect_boss:
        matchs = detect_mobs(insets=insets, anchor=anchor, type=MobType.BOSS)
    return len(matchs) > 0


@bot_status.run_if_enabled
def sleep_while_move_y(interval=0.02, n=15):
    player_y = bot_status.player_pos[1]
    count = 0
    while True:
        time.sleep(interval)
        if player_y == bot_status.player_pos[1]:
            count += 1
        else:
            count = 0
            player_y = bot_status.player_pos[1]
        if count == n:
            break


@bot_status.run_if_enabled
def sleep_in_the_air(interval=0.005, n=4, start_y=0):
    if shared_map.minimap_data is None or len(shared_map.minimap_data) == 0:
        sleep_while_move_y(interval, n)
        return
    count = 0
    step = 0
    while True:
        y = bot_status.player_pos[1] + 7
        x = bot_status.player_pos[0]
        value = shared_map.minimap_data[y][x]
        if value != 1 and value != 3:
            count = 0
        else:
            count += 1
        if count >= n:
            if start_y > 0:
                if start_y == bot_status.player_pos[1]:
                    break
                elif n < 8:
                    n = 8
                else:
                    break
            else:
                break
        step += 1
        if step >= 250:
            break
        time.sleep(interval)


def wait_until_map_changed(timeout=10):
    start = time.time()
    while (not bot_status.lost_minimap):
        time.sleep(0.5)
        print("not lost_minimap")

        if time.time() - start > timeout:
            return
    while (bot_status.lost_minimap):
        print("lost_minimap")
        time.sleep(0.5)
        if time.time() - start > timeout:
            return
    time.sleep(0.5)


def chenck_map_available(instance=True):
    if instance:
        start_time = time.time()
        while time.time() - start_time <= 5:
            if detect_mobs(capture.frame):
                return True
            time.sleep(0.1)
        return False
    else:
        for i in range(5):
            if bot_status.stage_fright:
                return False
            time.sleep(1)
        return True


def get_available_routines(command_name) -> list:
    routines = []
    folder = bot_settings.get_routines_dir(command_name)
    for root, ds, fs in os.walk(folder):
        for f in fs:
            if f.endswith(".csv"):
                routines.append(f[:-4])
    return routines



def identify_map_name():
    frame = utils.filter_color(capture.map_name_frame, TEXT_WHITE_RANGES)
    # utils.show_image(frame)
    
    file_path = f"{RESOURCES_DIR}/maps/maplestory_maps.xlsx"
    map_list = utils.iter_excel_calamine(file_path)
    available_map_names = map_list.keys()
    return utils.image_match_text(frame, available_map_names, 0.8, filter=[])


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


def convert_point_minimap_to_window(point: tuple[int, int]):
    '''convent the minimap point to the window point'''
    window_width = capture.window_rect.width
    window_height = capture.window_rect.height

    mini_height, mini_width, _ = capture.minimap_actual.shape

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


# -> tuple | tuple[int, int]:
def locate_player_fullscreen(accurate=False, frame=None, role_template=None):
    player_pos = convert_point_minimap_to_window(
        bot_status.player_pos)

    if accurate:
        if frame is None:
            frame = capture.frame
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

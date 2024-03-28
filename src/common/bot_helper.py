import time
from src.common import utils, bot_status, bot_settings
from src.common.constants import *
from src.common.image_template import *
from src.modules.capture import capture
from src.map.map import shared_map


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
            anchor = capture.convert_point_minimap_to_window(
                bot_status.player_pos)
        crop = frame[max(0, anchor[1]-insets.top):anchor[1]+insets.bottom,
                     max(0, anchor[0]-insets.left):anchor[0]+insets.right]
        # utils.show_image(crop)
    return detect_mobs(crop, type, multy_match, debug)


def detect_mobs(frame,
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


def chenck_map_available(instance=True):
    if instance:
        start_time = time.time()
        while time.time() - start_time <= 5:
            if detect_mobs(capture.fr):
                return True
            time.sleep(0.1)
        return False
    else:
        for i in range(5):
            if bot_status.stage_fright:
                return False
            time.sleep(1)
        return True


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

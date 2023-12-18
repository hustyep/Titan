from src.common import bot_status, bot_settings, utils


#############################
#      Helper Function      #
#############################


def direction_changed(direction) -> bool:
    if direction == 'left':
        return abs(bot_settings.boundary_point_r[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.boundary_point_l[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance


def edge_reached() -> bool:
    if abs(bot_settings.boundary_point_l[1] - bot_status.player_pos[1]) > 1:
        return
    if bot_status.player_direction == 'left':
        return abs(bot_settings.boundary_point_l[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.boundary_point_r[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance


def target_reached(start, target, tolerance=bot_settings.move_tolerance):
    # if tolerance > bot_settings.adjust_tolerance:
    #     return utils.distance(start, target) <= tolerance
    # else:
    return start[1] == target[1] and abs(start[0] - target[0]) <= tolerance


def find_next_point(start: tuple[int, int], target: tuple[int, int], tolerance: int):
    if map.minimap_data is None or len(map.minimap_data) == 0:
        return target

    if target_reached(start, target, tolerance):
        return

    d_x = target[0] - start[0]
    d_y = target[1] - start[1]
    if abs(d_x) <= tolerance:
        return target
    elif d_y < 0:
        tmp_x = (target[0], start[1])
        if target_reached(tmp_x, target, tolerance):
            return tmp_x
        if map.on_the_platform(tmp_x):
            return tmp_x
        tmp_y = (start[0], target[1])
        if map.is_continuous(tmp_y, target):
            return tmp_y
        return map.platform_point(tmp_x)
    else:
        # if abs(d_x) >= 20 and abs(d_y) >= 20:
        #     p = (start[0] + (20 if d_x > 0 else -20), target[1])
        #     if map.on_the_platform(p):
        #         return p
        tmp_x = (target[0], start[1])
        if map.is_continuous(tmp_x, target):
            return tmp_x
        tmp_y = (start[0], target[1])
        if map.on_the_platform(tmp_y):
            return tmp_y
        return map.platform_point(tmp_y)
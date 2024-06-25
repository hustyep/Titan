
import os

from src.common.constants import RESOURCES_DIR, Platform


def get_maps_dir(name):
    return os.path.join(RESOURCES_DIR, 'maps', name)


def platform_gap(platform1: Platform | None, platform2: Platform | None):
    if platform1 is None or platform2 is None:
        return -1
    if platform1.end_x < platform2.begin_x:
        return platform2.begin_x - platform1.end_x
    elif platform2.end_x < platform1.begin_x:
        return platform1.begin_x - platform2.end_x
    elif platform1.y == platform2.y:
        return 0
    else:
        return -1


def jumpable_platforms(platform1: Platform, platform2: Platform, max_gap_h=8, max_gap_v=8) -> bool:
    gap_h = platform_gap(platform1, platform2)
    gap_v = abs(platform1.y - platform2.y)
    if platform1.y == platform2.y:
        return gap_h <= max_gap_h and gap_v <= max_gap_v
    else:
        return gap_h in range(0, max_gap_h+1) and gap_v <= max_gap_v

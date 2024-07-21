from functools import wraps
from src.common.constants import MapPoint, Path

#################################
#       Global Variables        #
#################################

# Describes whether the main bot loop is currently running or not
enabled: bool = False

prepared: bool = False

acting: bool = False

started_time = None

# The player's status relative to the minimap
player_pos = MapPoint(0, 0)
player_direction = 'right'
player_moving = False

# Represents the current path that the bot is taking
path = []

current_path: Path | None = None

invisible = False
stage_fright = False
elite_boss_detected = False

lost_minimap = False
point_checking = False
white_room = False

# Rune status
rune_pos = None
rune_closest_pos = None
rune_solving = False


def reset():
    global white_room, player_pos, player_direction, path, lost_minimap, point_checking, rune_pos, rune_closest_pos, rune_solving, player_moving

    player_pos = MapPoint(0, 0)
    player_direction = 'right'
    player_moving = False
    path = []
    lost_minimap = False
    point_checking = False
    white_room = False

    rune_solving = False
    rune_pos = None
    rune_closest_pos = None


def run_if_enabled(function):
    """
    Decorator for functions that should only run if the bot is enabled.
    :param function:    The function to decorate.
    :return:            The decorated function.
    """
    @wraps(function)
    def helper(*args, **kwargs):
        if enabled:
            return function(*args, **kwargs)
    return helper


def run_if_disabled(message=''):
    """
    Decorator for functions that should only run while the bot is disabled. If MESSAGE
    is not empty, it will also print that message if its function attempts to run when
    it is not supposed to.
    """

    def decorator(function):
        def helper(*args, **kwargs):
            if not enabled:
                return function(*args, **kwargs)
            elif message:
                print(message)
        return helper
    return decorator

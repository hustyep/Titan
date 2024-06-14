from functools import wraps

#################################
#       Global Variables        #
#################################

# Describes whether the main bot loop is currently running or not
enabled: bool = False

prepared: bool = False

acting: bool = False

started_time = None

# The player's position relative to the minimap
player_pos = (0, 0)
player_direction = 'right'

# Represents the current path that the bot is taking
path = []

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

# Minal status
minal_pos = None
minal_closest_pos = None
mineral_type = None

# cube
cubing = False

def reset():
    global white_room, player_pos, player_direction, path, lost_minimap, point_checking, rune_pos, rune_closest_pos, rune_solving, minal_pos, minal_closest_pos, mineral_type

    player_pos = (0, 0)
    player_direction = 'right'
    path = []
    lost_minimap = False
    point_checking = False
    white_room = False
    
    rune_solving = False
    rune_pos = None
    rune_closest_pos = None
    
    minal_pos = None
    minal_closest_pos = None
    mineral_type = None

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
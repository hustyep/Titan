


#################################
#       Global Variables        #
#################################

# Describes whether the main bot loop is currently running or not
enabled: bool = False

started_time = None

# The player's position relative to the minimap
player_pos = (0, 0)
player_direction = 'right'

# Represents the current path that the bot is taking
path = []

invisible = False
stage_fright = False

# Rune status
rune_pos = None
rune_closest_pos = None
free = True

# Minal status
mining_enable = False
minal_pos = None
minal_closest_pos = None
mineral_type = None

def run_if_enabled(function):
    """
    Decorator for functions that should only run if the bot is enabled.
    :param function:    The function to decorate.
    :return:            The decorated function.
    """

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
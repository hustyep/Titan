from enum import Enum, auto
from typing import TypeVar

#########################
#       Constants       #
#########################

RESOURCES_DIR = 'resources'

MINIMAP_SCALE = 15

window_cap_top = 31
window_cap_botton = 8
window_cap_horiz = 8

################################
#       Bot Notification       #
################################


class BotFatal(Enum):
    WHITE_ROOM = 'White Room'
    CRASH = 'Crash'
    BLACK_SCREEN = 'Black Screen'


class BotError(Enum):
    DEAD = 'Dead'
    LOST_PLAYER = 'Lost Player'
    LOST_WINDOW = 'Lost Window'
    LOST_MINI_MAP = 'Lost Minimap'
    OTHERS_STAY_OVER_120S = 'Someone stay over 120s'


class BotWarnning(Enum):
    RUNE_INTERACT_FAILED = 'Rune Interact Failed'
    RUNE_FAILED = 'Rune Failed'
    OTHERS_COMMING = 'Someone\'s comming'
    OTHERS_STAY_OVER_30S = 'Someone stay over 30s'
    OTHERS_STAY_OVER_60S = 'Someone stay over 60s'
    BINDED = 'Binded'
    NO_MOVEMENT = 'No Movement'
    RUNE_ERROR = 'Rune Error'
    BACKGROUND = 'background'


class BotInfo(Enum):
    RUNE_ACTIVE = 'Rune Active'
    RUNE_LIBERATED = 'Rune Liberated'
    OTHERS_LEAVED = 'Someone\'s gone'


class BotVerbose(Enum):
    MINE_ACTIVE = 'Mine Active'
    BOSS_APPEAR = 'Boss Appear'
    BLIND = 'Blind'
    CALIBRATED = 'calibrated'
    NEW_FRAME = 'New Frame'


class BotDebug(Enum):
    SCREENSHOT_FAILED = 'Screenshot Failed'
    PLAYER_LOCATION_UPDATE = auto()

#############################
#       Mineral Type        #
#############################


class MineralType(Enum):
    HEART = 'heart mineral'
    CRYSTAL = 'crystal mineral'
    HERB_YELLOW = 'yellow herb'
    HERB_PURPLE = 'purple herb'


#############################
#       Role & Class        #
#############################
Name_Class_Map = {'Sllee': 'shadower',
                  'issl': 'night_lord',
                  'ggswift': 'shadower', }

#############################
#          Map Name         #
#############################
Map_Names = [
    "T-Boy's Resarch Train 1",
    'End Of The World 1-6',
    'End Of The World 1-7',
    'Outlaw-Infested Wastes 2',
    'Laboratory Behind Locked Door 1',
    'Ink-winged Owl',
]

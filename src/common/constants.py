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
#       Common Type        #
#############################


class AreaInsets:
    def __init__(self, top=0, bottom=0, left=0, right=0) -> None:
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right


class Rect:
    def __init__(self, x=0, y=0, width=0, height=0) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class MobType(Enum):
    NORMAL = 'normal mob'
    ELITE = 'elite mob'
    BOSS = 'boss mob'


class MineralType(Enum):
    HEART = 'heart mineral'
    CRYSTAL = 'crystal mineral'
    HERB_YELLOW = 'yellow herb'
    HERB_PURPLE = 'purple herb'


class BotRunMode(Enum):
    Farm = 'Farm'
    Daily = 'Daily'
    Cube = 'Cube'
    Mapping = 'Mapping'


#############################
#       Role & Class        #
#############################
Name_Class_Map = {'Sllee': 'shadower',
                  'issl': 'night_lord',
                  'ggswift': 'shadower',
                  'ermin': 'hero'}

Charactor_Daily_Map = {
    'Sllee': {
        'default': 'Harsh Winter 4',
        'quest': [
            'Train with No Destination 5',
            'Laboratory Behind Locked Door 1',
            'Combat Zone Outskirts 1',
            'Calm Beach 2',
            'Harsh Winter 4',
        ]
    },
    'issl': {
        'default': 'Harsh Winter 4',
        'quest': [
            'Train with No Destination 5',
            'Laboratory Behind Locked Door 1',
            'Combat Zone Outskirts 1',
            'Calm Beach 2',
            'Harsh Winter 4',
        ]},
    'ermin': {
        'default': 'Train with No Destination 5',
        'quest': [
            'Western City Ramparts in Battle 1',
            'Train with No Destination 5',
            "Road to the Castle's Gate 1",
        ]
    }
}

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

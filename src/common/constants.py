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
    IDENTIFY_ROLE_FAILED = 'Identify role failed'
    OTHERS_STAY_OVER_120S = 'Someone stay over 120s'


class BotWarnning(Enum):
    RUNE_FAILED = 'Rune Failed'
    BINDED = 'Binded'
    NO_MOVEMENT = 'No Movement'
    BACKGROUND = 'background'
    # not used
    RUNE_INTERACT_FAILED = 'Rune Interact Failed'
    OTHERS_COMMING = 'Someone\'s comming'
    OTHERS_STAY_OVER_30S = 'Someone stay over 30s'
    OTHERS_STAY_OVER_60S = 'Someone stay over 60s'


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


class MainStatType(Enum):
    STR = "STR"
    LUK = "LUK"
    INT = "INT"
    DEX = "DEX"


class CharacterType(Enum):
    Shadower = "shadower"
    NightLord = "night_lord"
    Hero = "hero"
    NightWalker = "night_walker"


class CharacterBranchType(Enum):
    Thief = "Thief"
    Warrior = "Warrior"
    Magician = "Magician"
    Bowman = "Bowman"
    Pirate = "Pirate"
    NONE = "NONE"


class CharacterGroupType(Enum):
    Explorer = "Explorer"
    Cygnus = "Cygnus"
    Resistance = "Resistance"
    Heroes = "Heroes"
    Nova = "Nova"
    Flora = "Flora"
    Other = "Other"


#############################
#       Role & Class        #
#############################
Name_Class_Map = {
    'Sllee': CharacterType.Shadower,
    'issl': CharacterType.NightLord,
    'ggswift': CharacterType.Shadower,
    'ermin': CharacterType.Hero
}

Charactor_Daily_Map = {
    'Sllee': {
        'default': 'Calm Beach 3',
        'quest': [
            'Train with No Destination 5',
            'Laboratory Behind Locked Door 1',
            'Combat Zone Outskirts 1',
            'Calm Beach 3',
            'Harsh Winter 4',
        ]
    },
    'issl': {
        'default': 'Harsh Winter 4',
        'quest': [
            'Laboratory Behind Locked Door 1',
            'Combat Zone Outskirts 1',
            'Calm Beach 2',
            'Harsh Winter 4',
        ]},
    'ermin': {
        'default': 'Laboratory Behind Locked Door 1',
        'quest': [
            'Western City Ramparts in Battle 1',
            'Train with No Destination 5',
            'Laboratory Behind Locked Door 1',
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
    'Ink-winged Owl',
    'Train with No Destination 5',
    'Laboratory Behind Locked Door 1',
    'Combat Zone Outskirts 1',
    'Calm Beach 2',
    'Harsh Winter 4',
]

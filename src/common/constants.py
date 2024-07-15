from enum import Enum, auto

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
    MAP_CHANGED = 'Map Changed'
    OTHERS_STAY_OVER_120S = 'Someone stay over 120s'


class BotWarnning(Enum):
    RUNE_FAILED = 'Rune Failed'
    BINDED = 'Binded'
    BLIND = 'Blind'
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
    BOSS_APPEAR = 'Boss Appear'


class BotVerbose(Enum):
    MINE_ACTIVE = 'Mine Active'
    CALIBRATED = 'calibrated'
    NEW_FRAME = 'New Frame'


class BotDebug(Enum):
    SCREENSHOT_FAILED = 'Screenshot Failed'
    PLAYER_LOCATION_UPDATE = auto()
    MOVE = 'move'

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


class MapPoint:
    def __init__(self, x: int, y: int, tolerance=3, tolerance_v=1):
        self.x = x
        self.y = y
        self.tolerance = tolerance
        self.tolerance_v = tolerance_v

    def __str__(self):
        return f"MapPoint: ({self.x}, {self.y}, {self.tolerance}, {self.tolerance_v})"

    @property
    def tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


class MapPointType(Enum):
    Unknown = -1
    Air = 0
    Floor = 1
    Rope = 2
    FloorRope = 3


class Portal:
    def __init__(self, entrance: MapPoint, export: MapPoint):
        self.entrance = entrance
        self.export = export


class Platform:
    def __init__(self, begin_x: int, end_x: int, y: int) -> None:
        self.begin_x = begin_x
        self.end_x = end_x
        self.y = y
        self.portals: list[Portal] = []

    def __str__(self) -> str:
        return f"({self.begin_x},{self.end_x}), {self.y}"

    @property
    def center(self):
        len = self.end_x - self.begin_x + 1
        return MapPoint(int((self.begin_x+self.end_x) / 2), self.y, int(len/2))


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
    Flame = 'Flame'
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
    'ermin': CharacterType.Hero,
    'heward': CharacterType.NightWalker
}

Charactor_Daily_Map = {
    'Sllee': {
        'default': 'Calm Beach 3',
        'quest': [
            'Train with No Destination 5',
            'Laboratory Behind Locked Door 1',
            'Combat Zone Outskirts 1',
            'Harsh Winter 4',
            'Calm Beach 3',
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
    },
    'heward': {
        'default': "Blooming Spring 2",
        'quest': [
            'Western City Ramparts in Battle 1',
            'Outlaw-Infested Wastes 2',
            'Laboratory Behind Locked Door 1'
        ]
    }
}

from command_book import *

class Keybindings(DefaultKeybindings):
    # Movement
    SHADOW_ASSAULT = 'g'

    # Buffs
    GODDESS_BLESSING = '1'
    EPIC_ADVENTURE = ''
    LAST_RESORT = '2'
    SHADOW_WALKER = 'shift'
    THROW_BLASTING = 'v'
    PICK_POCKET = 'f1'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = '='
    GUILD_POTION = "9"
    CANDIED_APPLE = '5'
    LEGION_WEALTHY = ''
    EXP_COUPON = '6'

    # Skills
    CRUEL_STAB = 'f'
    MESO_EXPLOSION = 'd'
    SUDDEN_RAID = 'r'
    DARK_FLARE = 'w'
    SHADOW_VEIL = 'x'
    ARACHNID = 'j'
    TRICKBLADE = 'a'
    SLASH_SHADOW_FORMATION = 'c'
    SONIC_BLOW = 'z'
    ERDA_SHOWER = '`'

class Shadower(CommandBook):
    def __init__(self):
        super().__init__(JobType.Shadower)
        # self.keybindings = Keybindings

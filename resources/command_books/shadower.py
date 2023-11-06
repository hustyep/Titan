"""A collection of all commands that Shadower can use to interact with the game. 	"""

from src.common import bot_status, bot_settings, utils
import time
import math
import threading
from src.command.commands import *
from src.map.map import map
from src.common.vkeys import *

# List of key mappings
class Keybindings(DefaultKeybindings):
    # Movement
    JUMP = 's'
    FLASH_JUMP = ';'
    SHADOW_ASSAULT = 'g'
    ROPE_LIFT = 'b'

    # Buffs
    GODDESS_BLESSING = '1'
    EPIC_ADVENTURE = ''
    LAST_RESORT = '2'
    MAPLE_WARRIOR = '3'
    SHADOW_WALKER = 'shift'
    THROW_BLASTING = 'v'
    FOR_THE_GUILD = '7'
    HARD_HITTER = '8'

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
    ERDA_SHOWER = '`'
    TRICKBLADE = 'a'
    SLASH_SHADOW_FORMATION = 'c'
    SONIC_BLOW = 'z'


#########################
#       Commands        #
#########################
def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """
        
    if bot_status.stage_fright and direction != 'up' and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    d_x = target[0] - bot_status.player_pos[0]
    d_y = target[1] - bot_status.player_pos[1]
    if direction == "up":
        MoveUp(dy=abs(d_y)).execute()
    elif direction == "down":
        MoveDown(dy=abs(d_y)).execute()
    elif abs(d_y) >= 26 and abs(d_x) >= 24 and ShadowAssault.usable_count() > 2:
        ShadowAssault(dx=d_x, dy=d_y).execute()
    elif abs(d_x) >= 26:
        HitAndRun(direction, target).execute()
    else:
        Walk(target_x=target[0]).execute()
        
    if edge_reached():
        print("edge reached")
        key_up(direction)
        if bot_status.player_direction == 'left':
            has_elite = detect_mobs(top=100,bottom=80,left=300,right=0)
        else:
            has_elite = detect_mobs(top=100,bottom=80,left=0,right=300)
        if has_elite is not None and len(has_elite) > 0:
            CruelStabRandomDirection().execute()
            
class HitAndRun(Command):
    def __init__(self, direction, target):
        super().__init__(locals())
        self.direction = direction
        self.target = target

    def main(self):
        d_x = self.target[0] - bot_status.player_pos[0]
        if bot_settings.mob_detect:
            if direction_changed():
                print("direction_changed")
                
                if time.time() - ErdaShower.castedTime > 5:
                    time.sleep(0.08)
                    key_up(self.direction)
                    time.sleep(0.5)
                    SlashShadowFormation().execute()
                    count = 0
                    while count < 80:
                        count += 1
                        has_boss = detect_mobs(top=180,bottom=-20,left=300,right=300,type=MobType.BOSS)
                        if has_boss is not None and len(has_boss) > 0:
                            SonicBlow().execute()
                        mobs = detect_mobs(top=350,bottom=50,left=1100,right=1100)
                        if mobs is not None and len(mobs) >= 2:
                            break
                    key_down(self.direction)                
            
            # threading.Thread(target=pre_detect, args=(self.direction,)).start()
            FlashJump(dx=abs(d_x)).execute()
            CruelStabRandomDirection().execute()
            sleep_in_the_air()
            # if config.elite_detected:
            #     SonicBlow().execute()
            #     config.elite_detected = False
        else:
            FlashJump(dx=abs(d_x)).execute()
            CruelStabRandomDirection().execute()
            # sleep_before_y(target_y=self.target[1])
            sleep_in_the_air(interval=0.018, n=5)
            
            
#########################
#        Y轴移动         #
#########################

class MoveUp(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        print(f"moveup dy={self.dy}")
        self.print_debug_info()

        if self.dy <= 6:
            press(Keybindings.JUMP)
            sleep_in_the_air()
        elif self.dy <= 24:
            JumpUp(dy=self.dy).execute()
        elif self.dy <= 40 and ShadowAssault().canUse():
            ShadowAssault('up', jump='True', distance=self.dy).execute()
        else:
            RopeLift(dy=self.dy).execute()


class MoveDown(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        self.print_debug_info()

        if self.dy >= 25 and ShadowAssault.usable_count() >= 3:
            ShadowAssault(direction='down', jump='True',
                          distance=self.dy).execute()
        else:
            time.sleep(0.2)
            key_down('down')
            press(Keybindings.JUMP, 1, down_time=0.1, up_time=0.5)
            sleep_in_the_air()
            key_up('down')
            # time.sleep(0.8 if self.dy >= 15 else 0.7)


class JumpUp(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        self.print_debug_info()

        time.sleep(0.5)
        
        evadeRope().execute()
        
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if self.dy >= 20 else 0.1)
        press(Keybindings.FLASH_JUMP, 1)
        key_up('up')
        sleep_in_the_air()
        # time.sleep(1.5)
        if map.on_the_rope(bot_status.player_pos):
            key_down('left')
            time.sleep(0.05)
            press(Keybindings.JUMP)
            key_up('left')

class FlashJump(Command):
    """Performs a flash jump in the given direction."""

    def __init__(self, time=1, dx=None):
        super().__init__(locals())

        if dx is not None:
            self.time = 2 if dx <= 32 else 2
        else:
            self.time = time

    def main(self):
        self.print_debug_info()

        if self.time == 1:
            press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.05)
        else:
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
        press(Keybindings.FLASH_JUMP, self.time, down_time=0.03, up_time=0.03)

class ShadowAssault(Command):
    """
    ShadowAssault in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """

    backswing = 0.15
    usable_times = 4
    cooldown = 60

    def __init__(self, direction='up', jump='True', distance=80, dx=None, dy=None):
        super().__init__(locals())
        if dx is None or dy is None:
            self.direction = direction
            self.jump = bot_settings.validate_boolean(jump)
            self.distance = bot_settings.validate_nonnegative_int(distance)
        else:
            if dy < 0 and dx < 0:
                self.direction = 'upleft'
                self.jump = True
            elif dy < 0 and dx > 0:
                self.direction = 'upright'
                self.jump = True
            elif dy > 0 and dx < 0:
                self.direction = 'downleft'
                self.jump = True
            elif dy > 0 and dx > 0:
                self.direction = 'downright'
                self.jump = True
            elif dy != 0:
                self.direction = 'up' if dy < 0 else 'down'
                self.jump = True
            elif dx != 0:
                self.direction = 'left' if dx < 0 else 'right'
                self.jump = False
            else:
                self.direction = direction
                self.jump = bot_settings.validate_boolean(jump)
            self.distance = math.sqrt(dx ** 2 + dy ** 2)

    @staticmethod
    def usable_count():
        if (time.time() - ShadowAssault.castedTime) > ShadowAssault.cooldown + ShadowAssault.backswing:
            return 4
        else:
            return ShadowAssault.usable_times

    def canUse(self, next_t: float = 0) -> bool:

        if self.__class__.usable_times > 0:
            return True

        cur_time = time.time()
        if (cur_time + next_t - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            return True

        return False

    def main(self):
        self.print_debug_info()

        if self.distance == 0:
            return

        # time.sleep(0.2)

        if self.direction.endswith('left'):
            if bot_status.player_direction != 'left':
                press('left', down_time=0.1)
        elif self.direction.endswith("right"):
            if bot_status.player_direction != 'right':
                press("right", down_time=0.1)
        elif self.direction == 'up':
            evadeRope().execute()
                
        if self.jump:
            if self.direction.startswith('down'):
                key_down('down')
                press(Keybindings.JUMP, 1, down_time=0.2, up_time=0.2)
                key_up("down")
            else:
                press(Keybindings.JUMP)
                time.sleep(0.1 if self.distance > 32 else 0.4)

        key_down(self.direction)
        time.sleep(0.05)

        cur_time = time.time()
        if (cur_time - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            self.__class__.castedTime = cur_time
            self.__class__.usable_times = 3
        else:
            self.__class__.usable_times -= 1
        press(Keybindings.SHADOW_ASSAULT)
        key_up(self.direction)
        time.sleep(self.backswing)
        sleep_in_the_air()
        # MesoExplosion().execute()
        
        # if bot_settings.record_layout:
        #     layout.add(*bot_status.player_pos)


# 绳索
class RopeLift(Command):
    key = Keybindings.ROPE_LIFT
    cooldown = 3

    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        self.print_debug_info()

        if self.dy >= 45:
            press(Keybindings.JUMP, up_time=0.2)
        elif self.dy >= 32:
            press(Keybindings.JUMP, up_time=0.1)
        press(self.__class__.key)
        sleep_in_the_air()
        # press(self.__class__.key, up_time=self.dy * 0.07)
        # if self.dy >= 32:
        #     time.sleep((self.dy - 32) * 0.01)


class CruelStab(Command):
    """Attacks using 'CruelStab' in a given direction."""

    def __init__(self, direction, attacks=2, repetitions=1):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)
        self.attacks = int(attacks)
        self.repetitions = int(repetitions)

    def main(self):
        self.print_debug_info()

        time.sleep(0.05)
        key_down(self.direction)
        time.sleep(0.05)
        if bot_status.stage_fright and utils.bernoulli(0.7):
            time.sleep(utils.rand_float(0.1, 0.3))
        for _ in range(self.repetitions):
            press(Keybindings.CRUEL_STAB, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class evadeRope(Command):
    def main(self):
        if map.near_rope(bot_status.player_pos):
            press(bot_status.player_direction, down_time=0.5)

#########################
#         Skills        #
#########################

class MesoExplosion(Command):
    """Uses 'MesoExplosion' once."""

    def main(self):
        press(Keybindings.MESO_EXPLOSION)


class CruelStabRandomDirection(Command):
    """Uses 'CruelStab' once."""
    backswing = 0.1

    def main(self):
        press(Keybindings.CRUEL_STAB, 1, up_time=0.2)
        MesoExplosion().execute()
        time.sleep(self.backswing)


class DarkFlare(Command):
    """
    Uses 'DarkFlare' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    cooldown = 57
    backswing = 0.8
    key = Keybindings.DARK_FLARE

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        self.print_debug_info()
        
        while not self.canUse():
            time.sleep(0.1)
        if self.direction is not None:
            press_acc(self.direction, down_time=0.03, up_time=0.03)
        super().main()


class ShadowVeil(Command):
    key = Keybindings.SHADOW_VEIL
    cooldown = 57
    precast = 0.3
    backswing = 0.9

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        self.print_debug_info()
        if self.direction is not None:
            press(self.direction)
        super().main()


class ErdaShower(Command):
    key = Keybindings.ERDA_SHOWER
    cooldown = 57
    backswing = 0.7

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        while not self.canUse():
            time.sleep(0.1)
        self.print_debug_info()
        if self.direction:
            press_acc(self.direction, down_time=0.03, up_time=0.1)
        key_down('down')
        press(Keybindings.ERDA_SHOWER)
        key_up('down')
        self.__class__.castedTime = time.time()
        time.sleep(self.__class__.backswing)
        

class SuddenRaid(Command):
    key = Keybindings.SUDDEN_RAID
    cooldown = 30
    backswing = 0.75

    def canUse(self, next_t: float = 0) -> bool:
        usable = super().canUse(next_t)
        if usable:
            mobs = detect_mobs(top=500,bottom=500,left=500,right=500,debug=False)
            return mobs is None or len(mobs) > 0
        else:
            return False
            
    # def main(self):
    #     used = super().main()
    #     if used:
    #         MesoExplosion().execute()
    #     return used

class Arachnid(Command):
    key = Keybindings.ARACHNID
    cooldown = 250
    backswing = 0.9


class TrickBlade(Command):
    key = Keybindings.TRICKBLADE
    cooldown = 14
    backswing = 0.7

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)
            
    def canUse(self, next_t: float = 0) -> bool:
        usable = super().canUse(next_t)
        if usable:
            mobs = detect_mobs(top=200,bottom=150,left=400,right=400)
            return mobs is None or len(mobs) > 0
        else:
            return False
    
    # def main(self):
    #     used = super().main()
    #     if used:
    #         MesoExplosion().execute()
    #     return used


class SlashShadowFormation(Command):
    key = Keybindings.SLASH_SHADOW_FORMATION
    cooldown = 90
    backswing = 0.8

class SonicBlow(Command):
    key = Keybindings.SONIC_BLOW
    cooldown = 45
    precast = 0.1
    backswing = 3

class PhaseDash(Command):
    key = 't'
    cooldown = 0
    backswing = 1


###################
#      Buffs      #
###################

class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            MAPLE_WARRIOR,
            GODDESS_BLESSING,
            LAST_RESORT,
            FOR_THE_GUILD,
            HARD_HITTER,
            SHADOW_WALKER,
        ]

    def main(self):
        for buff in self.buffs:
            if buff().canUse():
                buff().execute()
                break


class GODDESS_BLESSING(Command):
    key = Keybindings.GODDESS_BLESSING
    cooldown = 180
    precast = 0.3
    backswing = 0.85


class LAST_RESORT(Command):
    key = Keybindings.LAST_RESORT
    cooldown = 75
    precast = 0.3
    backswing = 0.8


class SHADOW_WALKER(Command):
    key = Keybindings.SHADOW_WALKER
    cooldown = 180
    precast = 0.3
    backswing = 0.8

    def main(self):
        super().main()
        bot_status.hide_start = time.time()


class EPIC_ADVENTURE(Command):
    key = Keybindings.EPIC_ADVENTURE
    cooldown = 120
    backswing = 0.75


class MAPLE_WARRIOR(Command):
    key = Keybindings.MAPLE_WARRIOR
    cooldown = 900
    backswing = 0.8


class FOR_THE_GUILD(Command):
    key = Keybindings.FOR_THE_GUILD
    cooldown = 3610
    backswing = 0.1

    def canUse(self, next_t: float = 0) -> bool:
        enabled = bot_status.gui_bot_settings.buffs.buff_bot_settings.get('Guild Buff')
        if not enabled:
            return False

        if time.time() - HARD_HITTER.castedTime <= 1800 and HARD_HITTER.castedTime > 0:
            return False

        return super().canUse(next_t)


class HARD_HITTER(Command):
    key = Keybindings.HARD_HITTER
    cooldown = 3610
    backswing = 0.1

    def canUse(self, next_t: float = 0) -> bool:
        enabled = bot_status.gui_bot_settings.buffs.buff_bot_settings.get('Guild Buff')
        if not enabled:
            return False

        if time.time() - FOR_THE_GUILD.castedTime <= 1800:
            return False

        return super().canUse(next_t)



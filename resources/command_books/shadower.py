"""A collection of all commands that Shadower can use to interact with the game. 	"""

import time
import math
from src.common.interfaces import AsyncTask
from src.command.commands import *
from src.common.vkeys import *
from src.common import bot_status, bot_settings, utils

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
def step(target, tolerance):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """

    d_x = target[0] - bot_status.player_pos[0]
    d_y = target[1] - bot_status.player_pos[1]
    if abs(d_x) in range(20, 28) and -d_y in range(25, 35):
        if ShadowAssault.usable_count() >= 2:
            ShadowAssault(target=target).execute()
            return
    if d_y in range(25, 35):
        if ShadowAssault.usable_count() >= 2:
            ShadowAssault(target=target).execute()
            return

    next_p = find_next_point(bot_status.player_pos, target, tolerance)
    if not next_p:
        return

    d_x = next_p[0] - bot_status.player_pos[0]
    d_y = next_p[1] - bot_status.player_pos[1]

    direction = None
    if abs(d_x) > tolerance:
        direction = 'right' if d_x > 0 else 'left'
    else:
        direction = 'down' if d_y > 0 else 'up'

    if direction == "up":
        move_up(next_p)
    elif direction == "down":
        move_down(next_p)
    elif abs(d_x) >= 26:
        hit_and_run(direction, target)
    else:
        Walk(target_x=target[0], tolerance=tolerance).execute()


def pre_detect(direction):
    result = detect_next_mob(direction, MobType.ELITE)
    if not result:
        result = detect_next_mob(direction, MobType.BOSS)
    return result


def detect_next_mob(direction, type):
    pos = map.minimap_to_window(bot_status.player_pos)
    if direction == 'right':
        has_elite = detect_mobs(
            anchor=pos, top=180, bottom=-20, left=-600, right=1000, type=type)
    else:
        has_elite = detect_mobs(
            anchor=pos, top=180, bottom=-20, left=1000, right=-600, type=type)
    return len(has_elite) > 0


@bot_status.run_if_enabled
def hit_and_run(direction, target):
    if bot_settings.mob_detect:
        if direction_changed() and time.time() - ErdaShower.castedTime > 5:
            print("direction_changed")
            key_down(direction)
            time.sleep(0.05)
            key_up(direction)
            time.sleep(0.5)
            # SlashShadowFormation().execute()
            count = 0
            while count < 80:
                count += 1
                pos = map.minimap_to_window(bot_status.player_pos)
                has_boss = detect_mobs(top=180, bottom=-20, left=300, right=300,
                                       anchor=pos,
                                       type=MobType.BOSS)
                if len(has_boss) > 0:
                    SonicBlow().execute()
                mobs = detect_mobs(top=350, bottom=50, left=1100, right=1100,
                                   anchor=pos)
                if len(mobs) >= 2:
                    break
        t = AsyncTask(target=pre_detect, args=(direction,))
        t.start()
        FlashJump(target=target, attack_if_needed=True).execute()
        elite_detected = t.join()
        if elite_detected:
            SonicBlow().execute()
    else:
        FlashJump(target=target, attack_if_needed=True).execute()


#########################
#        Y轴移动         #
#########################

@bot_status.run_if_enabled
def move_up(target):
    p = bot_status.player_pos
    dy = p[1] - target[1]
    if dy <= 0:
        return
    elif dy <= 7:
        press(Keybindings.JUMP)
        sleep_in_the_air()
    elif dy <= 24:
        JumpUp(target).execute()
    elif dy <= 40 and ShadowAssault().canUse():
        ShadowAssault(target=target).execute()
    else:
        RopeLift(dy).execute()


@bot_status.run_if_enabled
def move_down(target):
    p = bot_status.player_pos
    dy = p[1] - target[1]
    if dy >= 24 and ShadowAssault.usable_count() >= 3:
        ShadowAssault(direction='down', jump='True',
                      distance=dy).execute()
    else:
        sleep_in_the_air(n=1)
        if target[1] > bot_status.player_pos[1]:
            Fall().execute()


class JumpUp(Command):
    def __init__(self, target):
        super().__init__(locals())
        self.target = target

    def main(self):
        # TODO too long
        time.sleep(0.5)
        evade_rope(self.target)

        dy = bot_status.player_pos[1] - self.target[1]
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if dy >= 20 else 0.1)
        press(Keybindings.FLASH_JUMP, 1)
        key_up('up')
        sleep_in_the_air()


class FlashJump(Command):
    """Performs a flash jump in the given direction."""

    def __init__(self, target: tuple[int, int], attack_if_needed=False):
        super().__init__(locals())

        self.target = target
        self.attack_if_needed = attack_if_needed

    def detect_mob(self, direction):
        player_pos = map.minimap_to_window(bot_status.player_pos)
        mobs = []
        if direction == 'left':
            mobs = detect_mobs(anchor=player_pos, top=200,
                               left=600, right=0, bottom=100)
        else:
            mobs = detect_mobs(anchor=player_pos, top=200,
                               left=0, right=600, bottom=100)
        return mobs

    def main(self):
        dx = self.target[0] - bot_status.player_pos[0]
        dy = self.target[1] - bot_status.player_pos[1]
        direction = 'left' if dx < 0 else 'right'

        key_down(direction)
        if self.attack_if_needed:
            # detect = AsyncTask(
            #     target=self.detect_mob, args=(direction, ))
            # detect.start()
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
            # mobs_detected = detect.join()
            mobs_detected = True
            time = 2 if mobs_detected else 1
            press(Keybindings.FLASH_JUMP, time, down_time=0.03, up_time=0.03)
            if mobs_detected:
                CruelStab(True).execute()
        else:
            time = 2 if abs(dx) >= 32 else 1
            if dy < 0:
                press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.05)
            else:
                press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
            press(Keybindings.FLASH_JUMP, time, down_time=0.03, up_time=0.03)

        key_up(direction)
        sleep_in_the_air(n=1)


class ShadowAssault(Command):
    """
    ShadowAssault in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """

    backswing = 0.3
    usable_times = 4
    cooldown = 60

    def __init__(self, direction='up', jump='True', distance=80, target=None):
        super().__init__(locals())
        self.target = target
        if target is None:
            self.direction = direction
            self.jump = bot_settings.validate_boolean(jump)
            self.distance = bot_settings.validate_nonnegative_int(distance)
        else:
            dx = target[0] - bot_status.player_pos[0]
            dy = target[1] - bot_status.player_pos[1]
            if dy < 0 and abs(dx) >= 20:
                self.direction = 'upright' if dx > 0 else 'upleft'
                self.jump = True
            elif dy > 0 and abs(dx) >= 20:
                self.direction = 'downright' if dx > 0 else 'downleft'
                self.jump = True
            elif dy == 0:
                self.direction = 'left' if dx < 0 else 'right'
                self.jump = False
            else:
                self.direction = 'up' if dy < 0 else 'down'
                self.jump = True
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
            time.sleep(0.2)
            evade_rope(self.target)

        if self.jump:
            if self.direction.startswith('down'):
                key_down('down')
                press(Keybindings.JUMP, 1, down_time=0.2, up_time=0.2)
                key_up("down")
            else:
                press(Keybindings.JUMP)
                time.sleep(0.1 if self.distance > 32 else 0.4)

        key_down(self.direction)
        time.sleep(0.03)

        cur_time = time.time()
        if (cur_time - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            self.__class__.castedTime = cur_time
            self.__class__.usable_times = 3
        else:
            self.__class__.usable_times -= 1
        press(Keybindings.SHADOW_ASSAULT)
        key_up(self.direction)
        sleep_in_the_air()
        MesoExplosion().execute()
        time.sleep(self.backswing)

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

        if self.dy >= 45:
            press(Keybindings.JUMP, up_time=0.2)
        elif self.dy >= 32:
            press(Keybindings.JUMP, up_time=0.1)
        press(self.__class__.key)
        sleep_in_the_air(n=10)


#########################
#         Skills        #
#########################

class Attack(Command):
    def main(self):
        CruelStab().execute()


class CruelStab(Command):
    """Uses 'CruelStab' once."""
    backswing = 0.1

    def __init__(self, jumped=False):
        super().__init__(locals())
        self.jumped = jumped

    def main(self):
        press(Keybindings.CRUEL_STAB, 1, up_time=0.2)
        MesoExplosion().execute()
        time.sleep(0.5 if not self.jumped else self.backswing)


class MesoExplosion(Command):
    """Uses 'MesoExplosion' once."""

    def main(self):
        press(Keybindings.MESO_EXPLOSION, down_time=0.01, up_time=0.01)


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
            mobs = detect_mobs(top=500, bottom=500, left=500,
                               right=500, debug=False)
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
            mobs = detect_mobs(top=200, bottom=150, left=400, right=400)
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
        enabled = gui_setting.buff.get('Guild Buff')
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
        enabled = gui_setting.buff.get('Guild Buff')
        if not enabled:
            return False

        if time.time() - FOR_THE_GUILD.castedTime <= 1800:
            return False

        return super().canUse(next_t)

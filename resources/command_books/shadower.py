"""A collection of all commands that Shadower can use to interact with the game. 	"""

import time
import math
import threading
from src.common.interfaces import AsyncTask
from src.command.commands import *
from src.common.vkeys import *
from src.common import bot_status, bot_settings, utils, bot_helper
from src.models.map_model import Min_Jumpable_Gap, Max_Jumpable_Gap
from src.map.map_helper import *
from src.map.map import shared_map

# List of key mappings


class Keybindings:
    # Movement
    JUMP = 's'
    FLASH_JUMP = ';'
    SHADOW_ASSAULT = 'g'
    ROPE_LIFT = 'b'
    Go_Ardentmill = 'v'

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
    GOLD_POTION = ''
    GUILD_POTION = "9"
    CANDIED_APPLE = '8'
    LEGION_WEALTHY = '7'
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

#########################
#       Commands        #
#########################


def step(target: MapPoint, tolerance):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """

    d_x = target.x - bot_status.player_pos.x
    d_y = target.y - bot_status.player_pos.y
    if ShadowAssault.canUse():
        if abs(d_x) in ShadowAssault.x_range and -d_y in ShadowAssault.y_range:
            ShadowAssault(target=target).execute()
            return
        if d_y in ShadowAssault.y_range or d_y > 10 and abs(d_x) > 100:
            ShadowAssault(target=target).execute()
            return

    next_p = find_next_point(bot_status.player_pos, target)
    utils.log_event(f"[step]next_p:{str(next_p)}", bot_settings.debug)
    if not next_p:
        return

    if target_reached(bot_status.player_pos, target):
        return

    if target_reached(bot_status.player_pos, next_p):
        return

    bot_status.path = [bot_status.player_pos, next_p, target]

    d_y = next_p.y - bot_status.player_pos.y
    if abs(d_y) > 5:
        if d_y > 0:
            move_down(next_p)
        else:
            move_up(next_p)
    else:
        move_horizontal(next_p)


@bot_status.run_if_enabled
def move_horizontal(target: MapPoint):
    start_p = shared_map.fixed_point(bot_status.player_pos)
    d_x = target.x - start_p.x
    distance = abs(d_x)

    if not shared_map.is_continuous(start_p, target):
        DoubleJump(target=target, attack_if_needed=True).execute()
    elif distance >= DoubleJump.move_range.start:
        DoubleJump(target=target, attack_if_needed=True).execute()
    elif distance >= 15 or distance in range(7, 10):
        DoubleJump(target=target, attack_if_needed=False).execute()
    else:
        Walk(target).execute()

#########################
#        Y轴移动         #
#########################


@bot_status.run_if_enabled
def move_up(target: MapPoint):
    p = bot_status.player_pos
    dy = abs(p.y - target.y)

    up_point = MapPoint(p.x, target.y)
    if not shared_map.is_continuous(up_point, target):
        # 跨平台
        DoubleJump(target, False)
        return

    next_platform = shared_map.platform_of_point(target)
    assert (next_platform)
    if bot_status.player_moving and bot_status.player_direction == 'left':
        if up_point.x - next_platform.begin_x <= 8 and next_platform.end_x - next_platform.begin_x > 20:
            # move_horizontal(MapPoint(up_point.x+3, p.y, 2))
            press('right', down_time=0.1)
        time.sleep(0.2)
    elif bot_status.player_moving and bot_status.player_direction == 'right':
        if next_platform.end_x - up_point.x <= 10 and next_platform.end_x - next_platform.begin_x > 20:
            # move_horizontal(MapPoint(up_point.x-3, p.y, 2))
            press('left', down_time=0.1)
        time.sleep(0.2)

    if dy <= 0:
        return
    elif dy < 5:
        press(Keybindings.JUMP)
        sleep_in_the_air()
    elif dy < JumpUp.move_range.stop:
        JumpUp(target).execute()
    elif dy in ShadowAssault.y_range and ShadowAssault.canUse():
        ShadowAssault(target=target).execute()
    else:
        RopeLift(dy).execute()
        sleep_in_the_air(n=30)


@bot_status.run_if_enabled
def move_down(target: MapPoint):
    if target.y <= bot_status.player_pos.y:
        return
    if abs(bot_status.player_pos.y - target.y) <= 5:
        sleep_in_the_air()
        return
    platform_start = shared_map.platform_of_point(bot_status.player_pos)
    platform_target = shared_map.platform_of_point(target)
    assert platform_target
    if not platform_start:
        return
    dy = platform_target.y - platform_start.y
    if dy >= 24 and ShadowAssault.canUse():
        ShadowAssault(target=target).execute()
    else:
        next_p = MapPoint(bot_status.player_pos.x, target.y, 3)
        if shared_map.on_the_platform(next_p):
            Fall().execute()
        else:
            DoubleJump(target, False)


class JumpUp(Command):
    key = Keybindings.FLASH_JUMP
    type = SkillType.Move
    move_range = range(0, 24)

    def __init__(self, target: MapPoint):
        super().__init__(locals())
        self.target = target

    def main(self, wait=True):
        sleep_in_the_air(n=4)
        evade_rope()

        dy = bot_status.player_pos.y - self.target.y
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if dy >= 20 else 0.1)
        press(self.key, 1)
        key_up('up')
        sleep_in_the_air(n=10)
        return True


class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.FLASH_JUMP
    type = SkillType.Move
    cooldown = 0.2
    move_range = range(26, 35)
    config = {
        (20, 26): (0.2, 0.02),
        (26, 28): (0.02, 0.02),
        (28, 29): (0.06, 0.02),
        (29, 32): (0.06, 0.04, 0.02),
        (32, 35): (0.04, 0.05, 0.02),
    }

    def __init__(self, target: MapPoint | None = None, attack_if_needed=False):
        super().__init__(locals())

        self.target = target
        self.attack_if_needed = attack_if_needed

    def double_jump(self, t1, t2):
        press(Keybindings.JUMP, 1, down_time=0.02, up_time=t1)
        press(self.key, 1, down_time=0.02, up_time=t2)

    def triple_jump(self, t1, t2, t3):
        self.double_jump(t1, t2)
        press(self.key, 1, down_time=0.02, up_time=t3)

    def common_jump(self):
        self.double_jump(0.02, 0.02)

    def jumpe_with_config(self, times, direction):
        if len(times) == 2:
            self.double_jump(times[0], times[1])
        else:
            self.triple_jump(times[0], times[1], times[2])

    def time_config(self, distance: int):
        for range_tuple, value in self.config.items():
            if distance in range(range_tuple[0], range_tuple[1]):
                return value
        return (0.02, 0.02)

    def caculate_distance(self, target: MapPoint):
        start_p = shared_map.fixed_point(bot_status.player_pos)
        start_plat = shared_map.platform_of_point(start_p)
        target_plat = shared_map.platform_of_point(target)
        assert target_plat

        dx = target.x - start_p.x
        dy = target.y - start_p.y
        if start_plat == target_plat:
            return abs(dx)
        good_x = set()
        for x in range(target.x - target.tolerance, target.x + target.tolerance + 1):
            distance = abs(x - start_p.x)
            if dy in range(3, distance):
                distance -= dy
            if abs(x - target_plat.begin_x) > 2 and abs(x - target_plat.end_x) > 2:
                good_x.add(x)
        target_x = target.x
        if good_x:
            target_x = list(good_x)[randrange(0, len(good_x))]

        distance = abs(start_p.x - target_x)
        if dy in range(3, distance):
            distance -= dy
        return distance

    def main(self, wait=True):
        while not self.canUse():
            utils.log_event("double jump waiting", bot_settings.debug)
            time.sleep(0.01)

        if self.target is None:
            direction = random_direction()
            key_down(direction)
            time.sleep(0.02)
            self.common_jump()
            key_up(direction)
            sleep_in_the_air()
            return True

        dx = self.target.x - bot_status.player_pos.x
        dy = self.target.y - bot_status.player_pos.y
        direction = 'left' if dx < 0 else 'right'
        start_p = bot_status.player_pos
        distance = self.caculate_distance(self.target)

        self.__class__.castedTime = time.time()
        key_down(direction)
        time.sleep(0.02)
        need_check = False
        if dy < -5:
            if distance >= 20:
                self.triple_jump(0.06, 0.04, 0.04)
            else:
                self.double_jump(0.06, 0.04)
        else:
            self.common_jump()
        if self.attack_if_needed:
            CruelStab().execute()
        key_up(direction)
        sleep_in_the_air(n=1)
        p = bot_status.player_pos
        plat = shared_map.platform_of_point(self.target)
        if plat and abs(p.x - plat.begin_x) <= 2:
            press('right')
        elif plat and abs(p.x - plat.end_x) <= 2:
            press('left')
        if need_check and not target_reached(bot_status.player_pos, self.target):
            utils.log_event(
                f"[Failed][DoubleJump] distance={distance} start={start_p.tuple} end={bot_status.player_pos.tuple} target={str(self.target)}", True)
        return True


class ShadowAssault(Skill):
    """
    ShadowAssault in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """
    id = 'ShadowAssault'
    key = Keybindings.SHADOW_ASSAULT
    type = SkillType.Move
    backswing = 0.6
    max_times = 5
    usable_times = 0
    cooldown = 60
    ready = False
    x_range = range(0, 50)
    y_range = range(18, 42)

    def __init__(self, direction='up', jump='True', distance=80, target: MapPoint | None = None):
        super().__init__(locals())
        self.target = target
        if target is None:
            self.direction = direction
            self.jump = bot_settings.validate_boolean(jump)
            self.distance = bot_settings.validate_nonnegative_int(distance)
        else:
            dx = target.x - bot_status.player_pos.x
            dy = target.y - bot_status.player_pos.y
            if dy < 0 and abs(dx) >= 15:
                self.direction = 'upright' if dx > 0 else 'upleft'
                self.jump = True
            elif dy > 0 and abs(dx) >= 15:
                self.direction = 'downright' if dx > 0 else 'downleft'
                self.jump = abs(dy) > 25
            elif dy == 0:
                self.direction = 'left' if dx < 0 else 'right'
                self.jump = False
            else:
                self.direction = 'up' if dy < 0 else 'down'
                self.jump = True
            self.distance = math.sqrt(dx ** 2 + dy ** 2)

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[9:-2, 2:-12], threshold=0.98, debug=False)
        if matchs:
            cls.ready = True
            cls.usable_times = cls.max_times
        else:
            matchs = utils.multi_match(
                capture.buff_frame, cls.icon[2:-2, 2:-16], threshold=0.9)
            cls.ready = len(matchs) > 0
            if not cls.ready:
                cls.usable_times = 0
        # print(f"ShadowAssault: canuse={cls.ready}")

    def main(self, wait=True):
        if self.distance == 0:
            return False

        if not self.canUse():
            return False

        if self.jump:
            if self.direction.startswith('down'):
                key_down('down')
                time.sleep(0.01)
                press_acc(Keybindings.JUMP, down_time=0.2, up_time=0.1)
                key_up("down")
                time.sleep(0.01)
            else:
                if self.target is not None:
                    dy = self.target.y - bot_status.player_pos.y
                else:
                    dy = self.distance
                press(Keybindings.JUMP)
                if self.direction == 'up':
                    time.sleep(0.1 if abs(dy) >= 39 else 0.05)
                else:
                    time.sleep(0.2 if abs(dy) >= 39 else 0.05)

        key_down(self.direction)
        time.sleep(0.01)
        self.__class__.usable_times -= 1
        press(self.key)
        releaseAll()
        time.sleep(self.backswing)
        sleep_in_the_air()
        MesoExplosion().execute()
        return True


#########################
#         Skills        #
#########################

class Shadow_attack(Command):
    cooldown = 4

    def __init__(self, attack=True, direction=None):
        super().__init__(locals())
        self.attack = bot_settings.validate_boolean(attack)
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        assert (shared_map.current_map)
        while not self.canUse():
            time.sleep(0.1)
            mobs = detect_mobs(capture.frame, MobType.NORMAL, True)
            if len(mobs) == 0:
                return False

        n = 1
        self.__class__.castedTime = time.time()
        if Arachnid.canUse():
            Arachnid().execute()
        elif SolarCrest.canUse():
            SolarCrest().execute()
        elif SuddenRaid.canUse():
            SuddenRaid().execute()
        elif TrickBlade.canUse():
            TrickBlade(jump=True).execute()
            n = 2
        else:
            n = 3
            self.__class__.castedTime = time.time() - 1

        if self.attack and n > 0:
            for _ in range(0, n):
                direction = self.direction
                if direction is None:
                    direction = random_direction()
                Direction(direction).execute()
                if random() < 0.7:
                    Jump(0.1, attack=True).execute()
                else:
                    Attack().execute()
        else:
            time.sleep(0.5)
        return True

class Attack(Command):
    key = Keybindings.CRUEL_STAB
    type = SkillType.Attack

    def main(self, wait=True):
        return CruelStab().execute()


class Aoe(Skill):
    key = Keybindings.TRICKBLADE
    type = SkillType.Attack

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return TrickBlade.ready

    def main(self, wait=True):
        return TrickBlade().main()


class CruelStab(Skill):
    """Uses 'CruelStab' once."""
    key = Keybindings.CRUEL_STAB
    type = SkillType.Attack
    # cooldown = 0.5
    backswing = 0.001

    def main(self, wait=True):
        if not self.canUse():
            return False
        self.__class__.castedTime = time.time()
        jumped = not shared_map.on_the_platform(bot_status.player_pos)
        press_acc(self.key, 1, down_time=0.02, up_time=0.02)
        threading.Timer(0.3, MesoExplosion().execute, ).start()
        # MesoExplosion().execute()
        time.sleep(0.5 if not jumped else self.backswing)
        return True


class MesoExplosion(Skill):
    """Uses 'MesoExplosion' once."""
    key = Keybindings.MESO_EXPLOSION
    type = SkillType.Attack

    def main(self, wait=True):
        press_acc(self.key, down_time=0.005, up_time=0.01)
        return True


class DarkFlare(Skill):
    """
    Uses 'DarkFlare' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    key = Keybindings.DARK_FLARE
    type = SkillType.Summon
    cooldown = 58
    backswing = 0.8
    duration = 60

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if self.direction is not None:
            press_acc(self.direction, down_time=0.03, up_time=0.03)
        return super().main()


class ShadowVeil(Skill):
    key = Keybindings.SHADOW_VEIL
    type = SkillType.Summon
    cooldown = 57
    precast = 0.3
    backswing = 0.9
    duration = 12

    def __init__(self, direction='right'):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if self.direction is not None:
            press(self.direction)
        return super().main()


class SuddenRaid(Skill):
    key = Keybindings.SUDDEN_RAID
    cooldown = 30
    backswing = 0.75
    type = SkillType.Attack

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        usable = super().canUse()
        if not gui_setting.detection.detect_mob:
            return usable

        if usable:
            mobs = detect_mobs(capture.frame)
            return mobs is None or len(mobs) > 0
        else:
            return False

    # def main(self):
    #     used = super().main()
    #     if used:
    #         MesoExplosion().execute()
    #     return used

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[11:-2, 2:-2], threshold=0.9, debug=False)
        cls.ready = len(matchs) > 0


class TrickBlade(Skill):
    key = Keybindings.TRICKBLADE
    cooldown = 14
    backswing = 0.7
    type = SkillType.Attack

    def __init__(self, direction=None, jump=False):
        super().__init__(locals())
        self.direction = direction
        self.jump = bot_settings.validate_boolean(jump)

    def main(self, wait=True):
        if self.direction is not None:
            press_acc(self.direction, down_time=0.03, up_time=0.03)
        if self.jump:
            press(Keybindings.JUMP)
        return super().main()


class SlashShadowFormation(Skill):
    key = Keybindings.SLASH_SHADOW_FORMATION
    cooldown = 90
    backswing = 0.8
    type = SkillType.Attack


class SonicBlow(Skill):
    key = Keybindings.SONIC_BLOW
    cooldown = 45
    precast = 0.1
    backswing = 3
    type = SkillType.Attack


class PhaseDash(Skill):
    key = 't'
    cooldown = 0
    backswing = 1
    type = SkillType.Move


class PickPocket(Skill):
    key = Keybindings.PICK_POCKET
    type = SkillType.Switch
    cooldown = 1
    ready = False


class Steal(Skill):
    key = 'f3'
    type = SkillType.Switch
    cooldown = 1
    backswing = 2
    ready = False

###################
#      Buffs      #
###################


class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            MapleWarrior,
            MapleWorldGoddessBlessing,
            LastResort,
            ForTheGuild,
            HardHitter,
            ShadowWalker,
            Steal,
            PickPocket,
        ]

        LastResort.key = Keybindings.LAST_RESORT
        Arachnid.key = Keybindings.ARACHNID

    def main(self, wait=True):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!use buff")
        for buff in self.buffs:
            if buff.canUse():
                print(buff)
                result = buff().main(wait)
                if result:
                    return True
        return False


class ShadowWalker(Skill):
    key = Keybindings.SHADOW_WALKER
    cooldown = 180
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff


class EPIC_ADVENTURE(Skill):
    key = Keybindings.EPIC_ADVENTURE
    cooldown = 120
    backswing = 0.75
    type = SkillType.Buff


class Potion(Command):
    """Uses each of Shadowers's potion once."""

    def __init__(self):
        super().__init__(locals())
        self.potions = [
            GOLD_POTION,
            CANDIED_APPLE,
            GUILD_POTION,
            LEGION_WEALTHY,
            EXP_COUPON,
            EXP_Potion,
            Wealth_Potion,
        ]

        GOLD_POTION.key = Keybindings.GOLD_POTION
        CANDIED_APPLE.key = Keybindings.CANDIED_APPLE
        GUILD_POTION.key = Keybindings.GUILD_POTION
        LEGION_WEALTHY.key = Keybindings.LEGION_WEALTHY
        EXP_COUPON.key = Keybindings.EXP_COUPON
        Wealth_Potion.key = Keybindings.WEALTH_POTION
        EXP_Potion.key = Keybindings.EXP_POTION

    def main(self, wait=True):
        if bot_status.invisible:
            return False
        for potion in self.potions:
            if potion.canUse():
                potion().execute()
                time.sleep(0.2)
        return True


@bot_status.run_if_enabled
def find_next_point(start: MapPoint, target: MapPoint):
    # utils.log_event(f"[find_next_point] start:{start.tuple} target:{str(target)}", bot_settings.debug)

    if shared_map.minimap_data is None or len(shared_map.minimap_data) == 0:
        return target

    if shared_map.current_map is None:
        return target

    if target_reached(start, target):
        return

    start = shared_map.fixed_point(start)
    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return

    if platform_start == platform_target:
        return target

    paths = shared_map.path_between(start, target, bot_status.stage_fright and gui_setting.auto.action)
    utils.log_event(f"[find_next_point] paths:", bot_settings.debug)
    if paths:
        for plat in paths:
            utils.log_event(f"  {str(plat)}", bot_settings.debug)
        next_platform = paths[1]
        d_y = next_platform.y - platform_start.y

        tmp_p = next_platform.center
        if len(paths) == 2:
            portal = shared_map.current_map.platform_portable(platform_start, platform_target)
            if portal:
                if target_reached(start, portal.entrance):
                    return portal.export
                else:
                    return portal.entrance
            tmp_p = target
        if abs(d_y) <= 5:
            next_p = find_next_horizontal_point(start, tmp_p)
            if next_p:
                return next_p
        elif d_y < 0:
            next_p = find_next_upper_point(start, tmp_p)
            if next_p:
                return next_p
        else:
            next_p = find_next_under_point(start, tmp_p)
            if next_p:
                return next_p
    return shared_map.platform_point(MapPoint(target.x, target.y - 1, 3))


def find_next_horizontal_point(start: MapPoint, target: MapPoint):
    # if start.y != target.y:
    #     return

    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return
    if platform_start == platform_target:
        return target

    max_distance = Max_Jumpable_Gap
    target_range = None
    if platform_start.end_x < platform_target.begin_x:
        target_range = range(max(platform_target.begin_x - max_distance,
                             platform_start.begin_x), platform_start.end_x + 1)
    else:
        target_range = range(platform_start.begin_x, min(
            platform_target.end_x + max_distance, platform_start.end_x) + 1)
    if start.x in target_range:
        return target
    else:
        target_x = (target_range.start + target_range.stop) / 2
        tolerance = (target_range.stop - target_range.start) / 2
        if platform_start.end_x < platform_target.begin_x:
            if abs(target_range.start - start.x) <= 10 and abs(platform_start.end_x - start.x) > 14:
                target_x = platform_start.end_x - 4
                tolerance = 4
        else:
            if abs(target_range.stop - start.x) <= 10 and abs(platform_start.begin_x - start.x) > 14:
                target_x = platform_start.begin_x + 4
                tolerance = 4
        return MapPoint(int(target_x), start.y, int(tolerance))


def find_next_upper_point(start: MapPoint, target: MapPoint):
    if start.y <= target.y:
        return

    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return

    gap = platform_gap(platform_start, platform_target)
    if gap <= -5:
        # 有交集
        # 优先垂直方向接近
        next_p = MapPoint(start.x, platform_target.y, 3)
        if shared_map.is_continuous(next_p, target):
            if target_reached(next_p, target):
                return next_p
            return target

        # 尝试水平方向接近
        next_p = MapPoint(target.x, start.y, target.tolerance)
        if not shared_map.is_continuous(start, next_p):
            next_p = None
        if next_p:
            if target_reached(start, next_p):
                return target
            else:
                if next_p.x < start.x:
                    if next_p.x - platform_start.begin_x <= 3:
                        next_p = None
                else:
                    if platform_start.end_x - next_p.x <= 3:
                        next_p = None
                if next_p:
                    return next_p

        intersection_point = point_of_intersection(platform_start, platform_target)
        assert (intersection_point)
        if target_reached(start, intersection_point):
            return target
        else:
            return intersection_point
    else:
        # 二段跳范围内
        if platform_start.end_x < platform_target.begin_x:
            next_p = MapPoint(platform_start.end_x - 2, platform_start.y, 3)
        else:
            next_p = MapPoint(platform_start.begin_x + 2, platform_start.y, 3)
        if target_reached(start, next_p):
            return target
        else:
            return next_p


def find_next_under_point(start: MapPoint, target: MapPoint):
    if start.y >= target.y:
        return

    assert (shared_map.current_map)
    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return

    intersections = set(platform_start.x_range).intersection(set(platform_target.x_range))

    if target.x in intersections:
        return find_fall_point(start, target)
    if shared_map.current_map.can_jump_down(platform_start, platform_target):
        return find_jump_down_point(start, target)
    return find_fall_point(start, target)


def find_fall_point(start: MapPoint, target: MapPoint):
    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    assert (shared_map.current_map)
    assert platform_start
    assert platform_target

    gap = platform_gap(platform_start, platform_target)
    if gap <= -Min_Jumpable_Gap:
        available_x = set(platform_start.x_range).intersection(set(platform_target.x_range))
        for y in [y for y in shared_map.current_map.platform_map.keys() if y in range(start.y + 1, target.y)]:
            plats = shared_map.current_map.platforms_of_y(y)
            assert (plats)
            for plat in plats:
                available_x = available_x.difference(set(plat.x_range))
        if len(available_x) > 0:
            if start.x in available_x:
                Fall().execute()
                return None
            else:
                next_p = point_of_intersection(platform_start, platform_target)
                assert next_p
                if target_reached(start, next_p):
                    next_p.tolerance = 2
                return next_p


def find_jump_down_point(start: MapPoint, target: MapPoint):
    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    assert (shared_map.current_map)
    assert platform_start
    assert platform_target

    dy = platform_target.y - platform_start.y
    max_jump_distance = 30 + dy
    gap = platform_gap(platform_start, platform_target)
    available_x = 0
    if platform_target.end_x > platform_start.end_x:
        if gap < 0:
            available_x = platform_start.end_x - max_jump_distance
        else:
            available_x = platform_target.begin_x - max_jump_distance
        available_x = max(available_x, platform_start.begin_x)
        x = (available_x + platform_start.end_x)/2
        tolorance = (platform_start.end_x - available_x + 1)/2
        next_p = MapPoint(int(x), start.y, int(tolorance))
        tmp_p = MapPoint(platform_start.end_x + 20, target.y, 10)
        if target_reached(start, next_p):
            return target if target_reached(target, tmp_p) else tmp_p
        else:
            return next_p
    else:
        if gap < 0:
            available_x = platform_start.begin_x + max_jump_distance
        else:
            available_x = platform_target.end_x + max_jump_distance
        available_x = min(available_x, platform_start.end_x)
        x = (platform_start.begin_x + available_x)/2
        tolorance = (available_x - platform_start.begin_x + 1)/2
        next_p = MapPoint(int(x), start.y, int(tolorance))
        tmp_p = MapPoint(platform_start.begin_x - 20, target.y, 10)
        if target_reached(start, next_p):
            return target if target_reached(target, tmp_p) else tmp_p
        else:
            return next_p

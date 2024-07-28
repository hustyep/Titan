"""A collection of all commands that Night Walker can use to interact with the game. 	"""

import time
from random import randrange
import cv2

from src.common import bot_status, bot_settings, utils
from src.common.gui_setting import gui_setting
from src.common.vkeys import press, key_down, key_up, releaseAll, press_acc
from src.routine.components import *
from src.command.commands import *  # type: ignore
# from src.command.commands import Command, Skill, Walk, Fall, Direction, RopeLift, Arachnid, LastResort, ForTheGuild, HardHitter, SkillType, sleep_in_the_air, target_reached, evade_rope, opposite_direction, detect_mobs_around_anchor
from src.map.map_helper import *
from src.map.map import shared_map
from src.modules.capture import capture
from src.chat_bot.chat_bot import chat_bot
from src.models.map_model import Min_Jumpable_Gap, Max_Jumpable_Gap

# List of key mappings


class Keybindings:
    # Movement
    JUMP = 's'
    Shadow_Jump = 'g'
    Shadow_Dodge = 'a'
    ROPE_LIFT = 'b'

    # Buffs
    Transcendent_Cygnus_Blessing = '1'
    Glory_of_the_Guardians = '2'
    Shadow_Illusion = '3'
    LAST_RESORT = '4'
    Shadow_Spear = 'v'
    Shadow_Bat = 'f1'
    Dark_Elemental = 'f3'
    Darkness_Ascending = '6'
    FOR_THE_GUILD = '8'
    HARD_HITTER = '7'
    Cygnus_Knights_Will = 'end'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "="
    GOLD_POTION = ""
    GUILD_POTION = "n"
    CANDIED_APPLE = '9'
    LEGION_WEALTHY = ''
    EXP_COUPON = '-'

    # Skills
    Quintuple_Star = 'f'
    Dark_Omen = 'r'
    Dominion = 'c'
    ERDA_SHOWER = '`'
    Phalanx_Charge = 'z'
    Greater_Dark_Servant = 'd'
    Shadow_Bite = 'e'
    Rapid_Throw = 'x'
    Silence = 'j'
    ARACHNID = 'w'
    SolarCrest = '5'


#########################
#       Movement        #
#########################


@bot_status.run_if_enabled
def step(target: MapPoint):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """

    # utils.log_event(f"[step]target:{str(target)}", bot_settings.debug)
    next_p = find_next_point(bot_status.player_pos, target)
    utils.log_event(f"[step]next_p:{str(next_p)}", bot_settings.debug)
    if not next_p:
        return

    bot_status.path = [bot_status.player_pos, next_p, target]

    portal = shared_map.point_portable(bot_status.player_pos, next_p)
    if portal:
        Use_Portal(portal).execute()
        return

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
    elif distance >= Shadow_Dodge.move_range.start:
        Shadow_Dodge('left' if d_x < 0 else 'right').execute()
    else:
        Walk(target).execute()


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
        if up_point.x - next_platform.begin_x <= 8:
            # move_horizontal(MapPoint(up_point.x+3, p.y, 2))
            press('right', down_time=0.2)
        else:
            time.sleep(0.2)
    elif bot_status.player_moving and bot_status.player_direction == 'right':
        if next_platform.end_x - up_point.x <= 10:
            # move_horizontal(MapPoint(up_point.x-3, p.y, 2))
            press('left', down_time=0.2)
        else:
            time.sleep(0.2)

    if dy < 5:
        press(Keybindings.JUMP)
    elif dy < Jump_Up.move_range.stop:
        Jump_Up(target).execute()
    else:
        Shadow_Rope_Lift(target).execute()


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
    intersections = set(platform_start.x_range).intersection(set(platform_target.x_range))
    if target.x in intersections:
        next_p = MapPoint(bot_status.player_pos.x, target.y, 3)
        if shared_map.on_the_platform(next_p):
            Fall().execute()
        else:
            DoubleJump(target, False)
    else:
        DoubleJump(target, False)


#########################
#        Y轴移动         #
#########################

class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    cooldown = 0.2
    backswing = 0
    move_range = range(26, 47)
    config = {
        (7, 8): (0.01, 0.02, 0.02, 0.01),
        (8, 10): (0.10, 0.02, 0.02, 0.02),
        (10, 11): (0.20, 0.02, 0.02, 0.02),

        (15, 16): (0.20, 0.05, 0.1, 0.02),
        (16, 17): (0.10, 0.10, 0.1, 0.02),
        (17, 18): (0.20, 0.10, 0.1, 0.02),
        (18, 19): (0.15, 0.12, 0.1, 0.02),
        (19, 21): (0.10, 0.16, 0.1, 0.02),
        (21, 23): (0.10, 0.25, 0.1, 0.02),
        (23, 26): (0.20, 0.20, 0.1, 0.10),
        # 1代表shadow_dodge
        (26, 28): (0.01, 0.10, 1),
        (28, 29): (0.06, 0.04),
        (29, 32): (0.06, 0.04, 0.04),
        (32, 34): (0.01, 0.1, 0.1, 1),
        (34, 35): (0.04, 0.05, 0.05),
        (35, 38): (0.01, 0.1, 0.15, 1),
        (38, 41): (0.01, 0.1, 0.2, 1),
        (41, 44): (0.01, 0.2, 0.2, 1),
        (44, 47): (0.01, 0.3, 0.2, 1),
    }

    def __init__(self, target: MapPoint | None = None, attack_if_needed=False):
        super().__init__(locals())
        self.target = target
        self.attack_if_needed = attack_if_needed

    def time_config(self, distance: int):
        for range_tuple, value in self.config.items():
            if distance in range(range_tuple[0], range_tuple[1]):
                return value
        return (0.02, 0.02, 0.02, 0.02)

    def double_jump(self, t1, t2):
        press(Keybindings.JUMP, 1, down_time=0.02, up_time=t1)
        press(self.key, 1, down_time=0.02, up_time=t2)

    def triple_jump(self, t1, t2, t3):
        self.double_jump(t1, t2)
        press(self.key, 1, down_time=0.02, up_time=t3)

    def common_jump(self):
        self.double_jump(0.01, 0.02)

    def scram(self, direction, down_time, up_time):
        key_up(direction)
        time.sleep(0.01)
        press_acc(opposite_direction(direction), down_time=down_time, up_time=up_time)
        press(self.key, 1, down_time=0.02, up_time=0.01)

    def jumpe_with_config(self, times, direction):
        if len(times) == 2:
            self.double_jump(times[0], times[1])
        elif len(times) == 3:
            if times[2] == 1:
                self.attack_if_needed = False
                self.double_jump(times[0], times[1])
                Shadow_Dodge(direction, wait=False).execute()
            else:
                self.triple_jump(times[0], times[1], times[2])
        elif len(times) == 4:
            self.attack_if_needed = False
            if times[3] == 1:
                self.triple_jump(times[0], times[1], times[2])
                Shadow_Dodge(direction, wait=False).execute()
            else:
                self.double_jump(times[0], times[1])
                self.scram(direction, times[2], times[3])

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
        distance = abs(dx)

        self.__class__.castedTime = time.time()
        key_down(direction)
        time.sleep(0.02)
        need_check = False
        if dy < -5:
            if distance >= 20:
                self.triple_jump(0.06, 0.04, 0.04)
            else:
                self.double_jump(0.06, 0.04)
        elif abs(dy) <= 5 and not shared_map.is_continuous(start_p, self.target):
            if distance >= 44:
                distance = 44
            elif distance < 16:
                distance = 16
            times = self.time_config(distance)
            self.jumpe_with_config(times, direction)
        elif distance <= 46:
            times = self.time_config(distance)
            self.jumpe_with_config(times, direction)
            need_check = True
        else:
            self.common_jump()
        if self.attack_if_needed:
            press(Keybindings.Quintuple_Star, down_time=0.01, up_time=0.01)
        key_up(direction)
        sleep_in_the_air(n=1)
        if need_check and not target_reached(bot_status.player_pos, self.target):
            utils.log_event(
                f"[Failed][DoubleJump] start={start_p.tuple} end={bot_status.player_pos.tuple} target={str(self.target)}", True)
        return True


# 上跳
class Jump_Up(Command):
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    move_range = range(0, 29)

    def __init__(self, target: MapPoint):
        super().__init__(locals())
        self.target = target

    def main(self, wait=True):
        sleep_in_the_air(n=4)
        dy = bot_status.player_pos.y - self.target.y
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if dy >= 20 else 0.3)
        press(Keybindings.JUMP)
        time.sleep(0.5)
        key_up('up')
        dx = self.target.x - bot_status.player_pos.x
        direction = 'left' if dx < 0 else 'right'
        if not shared_map.on_the_platform(MapPoint(bot_status.player_pos.x, self.target.y), 1):
            key_down(direction)
            time.sleep(0.02)
            press(Keybindings.Shadow_Jump)
            time.sleep(0.02)
            key_up(direction)
        elif abs(dx) > self.target.tolerance:
            if abs(dx) >= 20:
                key_down(direction)
                time.sleep(0.02)
                press(Keybindings.Shadow_Jump)
                time.sleep(0.02)
                key_up(direction)
            elif abs(dx) >= Shadow_Dodge.move_range.start:
                Shadow_Dodge(direction, wait=False).execute()
            elif abs(dx) >= 8:
                key_down(direction)
                time.sleep(0.1)
                press(Keybindings.Shadow_Jump)
                time.sleep(0.05)
                key_up(direction)
        sleep_in_the_air(n=2, detect_rope=True)
        return True


class Shadow_Rope_Lift(Command):
    '''自定义绳索'''
    key = DefaultKeybindings.ROPE_LIFT
    type = SkillType.Move
    cooldown = 3

    def __init__(self, target: MapPoint):
        super().__init__(locals())
        self.target = target

    def main(self, wait=True):
        RopeLift(self.target.y).execute()
        start_time = time.time()
        while bot_status.player_pos.y > self.target.y:
            time.sleep(0.1)
            if time.time() - start_time > 3:
                DoubleJump().execute()
                break
        dx = self.target.x - bot_status.player_pos.x
        direction = 'left' if dx < 0 else 'right'
        if abs(dx) >= 30:
            press(direction)
            press(Keybindings.Shadow_Jump)
        elif abs(dx) >= Shadow_Dodge.move_range.start:
            Shadow_Dodge(direction, wait=False).execute()
        sleep_in_the_air(n=10)
        return True

#########################
#        X轴移动         #
#########################


class Shadow_Dodge(Skill):
    key = Keybindings.Shadow_Dodge
    type = SkillType.Move
    cooldown = 0
    precast = 0
    backswing = 0.3
    move_range = range(10, 15)
    # 12-14

    def __init__(self, direction='right', wait=True):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)
        self.wait = bot_settings.validate_boolean(wait)

    def main(self, wait=True):
        if not self.canUse():
            return False

        releaseAll()
        self.__class__.castedTime = time.time()
        press(opposite_direction(self.direction), down_time=0.1)
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        # press(self.direction)
        if self.wait:
            sleep_in_the_air()
        return True

#######################
#       Summon        #
#######################


class Greater_Dark_Servant(Skill):
    key = Keybindings.Greater_Dark_Servant
    type = SkillType.Summon
    cooldown = 60
    precast = 0.4
    backswing = 0.3
    duration = 55
    tolerance = 1

    def main(self, wait=True):
        while not self.canUse():
            Shadow_Attack().execute()
        # Dark_Omen().execute()
        return super().main(wait)


class Replace_Dark_Servant(Skill):
    key = Keybindings.Greater_Dark_Servant
    type = SkillType.Move
    cooldown = 1
    backswing = 0.6

    def __init__(self, resummon='False'):
        super().__init__(locals())
        self.resummon = bot_settings.validate_boolean(resummon)

    def main(self, wait=True):
        if self.resummon and not self.canUse():
            return False
        if self.resummon:
            key_down('down')
            time.sleep(0.01)
        result = super().main(wait)
        if self.resummon:
            key_up('down')
        time.sleep(0.5)
        return result


#######################
#       Skills        #
#######################

class HEXA_Shadow_Bat(Skill):
    key = Keybindings.Shadow_Bat
    type = SkillType.Switch
    cooldown = 1
    ready = False


class Dark_Elemental(Skill):
    key = Keybindings.Dark_Elemental
    type = SkillType.Switch
    cooldown = 1
    ready = False


class Darkness_Ascending(Skill):
    key = Keybindings.Darkness_Ascending
    type = SkillType.Buff
    cooldown = 1800
    ready = False


class Quintuple_Star(Skill):
    key = Keybindings.Quintuple_Star
    type = SkillType.Attack
    backswing = 0.55


class Dark_Omen(Skill):
    key = Keybindings.Dark_Omen
    type = SkillType.Attack
    cooldown = 20
    backswing = 0.7
    tolerance = 1


class Shadow_Bite(Skill):
    key = Keybindings.Shadow_Bite
    type = SkillType.Attack
    cooldown = 15
    backswing = 0.7
    tolerance = 0.9

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        last_state = cls.ready
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.98)
        cls.ready = len(matchs) > 0
        if not cls.ready or cls.ready != last_state:
            cls.update_time = time.time()


class Dominion(Skill):
    key = Keybindings.Dominion
    type = SkillType.Attack
    cooldown = 175
    precast = 0.1
    backswing = 0.1
    tolerance = 5

    def main(self, wait=True):
        if not self.canUse():
            return False
        self.__class__.castedTime = time.time()
        press(self.__class__.key, down_time=self.__class__.precast, up_time=self.__class__.backswing)
        Shadow_Dodge().execute()
        return True


class Phalanx_Charge(Skill):
    key = Keybindings.Phalanx_Charge
    type = SkillType.Attack
    cooldown = 30
    precast = 0.1
    backswing = 0.75
    tolerance = 0.5

    def __init__(self, direction='none'):
        super().__init__(locals())
        if direction == 'none' or direction == None:
            self.direction = None
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if not self.canUse():
            return False
        if self.direction is not None:
            Direction(self.direction).execute()
        return super().main(wait)


class Silence(Skill):
    key = Keybindings.Silence
    type = SkillType.Attack
    cooldown = 350
    precast = 0.3
    backswing = 3
    tolerance = 6


class Rapid_Throw(Skill):
    key = Keybindings.Rapid_Throw
    type = SkillType.Attack
    cooldown = 90
    precast = 0.5
    backswing = 2
    tolerance = 5

    def main(self, wait=True):
        if not self.canUse():
            return False
        time.sleep(self.precast)
        self.castedTime = time.time()
        for _ in range(0, 10):
            press(self.key)
            time.sleep(0.3)
        time.sleep(self.backswing)
        return True


class Cygnus_Knights_Will(Command):
    key = Keybindings.Cygnus_Knights_Will
    type = SkillType.Buff
    cooldown = 300
    precast = 0.3
    backswing = 0.6
    tolerance = 5


####################
#      Actions     #
####################


class Attack(Command):
    key = Quintuple_Star.key
    type = SkillType.Attack
    backswing = Quintuple_Star.backswing

    def main(self, wait=True):
        return Quintuple_Star().execute()


class Shadow_Attack(Command):
    cooldown = 4.5

    def __init__(self, attack=True, direction=None):
        super().__init__(locals())
        self.attack = bot_settings.validate_boolean(attack)
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        assert (shared_map.current_map)
        while not self.canUse() and not bot_status.elite_boss_detected:
            time.sleep(0.1)
            mobs = detect_mobs(capture.frame, MobType.NORMAL, True)
            if len(mobs) == 0:
                return False

        if bot_status.elite_boss_detected:
            start_time = time.time()
            while bot_status.elite_boss_detected:
                Burst().execute()
                if time.time() - start_time >= 30:
                    break
            return True

        start_time = time.time()
        if start_time - Shadow_Bite.castedTime >= 5 and not bot_status.elite_boss_detected:
            while not Shadow_Bite.canUse():
                time.sleep(0.1)
                mobs = detect_mobs(capture.frame, MobType.NORMAL, True)
                if len(mobs) == 0:
                    return False
                if time.time() - start_time > 5:
                    break

        n = 0
        self.__class__.castedTime = time.time()
        if Shadow_Bite.canUse():
            Shadow_Bite().execute()
        elif Dominion.canUse():
            Dominion().execute()
        elif Arachnid.canUse():
            Arachnid().execute()
        elif SolarCrest.canUse():
            SolarCrest().execute()
        elif Dark_Omen.canUse():
            Dark_Omen().execute()
            n = 2
        else:
            n = 0
            self.__class__.castedTime = time.time() - self.cooldown

        direction = self.direction
        if direction is None:
            direction = random_direction()
        if self.attack and n > 0:
            Direction(direction).execute()
            key_down(Keybindings.Quintuple_Star)
            time.sleep(n)
            key_up(Keybindings.Quintuple_Star)
            time.sleep(Quintuple_Star.backswing)
        else:
            time.sleep(0.5)
        return True


class Pre_Burst(Command):
    def main(self, wait=True):
        Dominion().execute()
        p = shared_map.platform_point(bot_status.player_pos)
        plat = shared_map.platform_of_point(p)
        assert (plat)
        if p.x - plat.begin_x <= plat.end_x - p.x:
            Move(plat.begin_x + 3, plat.y, 3).execute()
        else:
            Move(plat.end_x - 3, plat.y, 3).execute()
        Shadow_Spear().execute()
        Shadow_Illusion().execute()
        if time.time() - self.castedTime > 30:
            Replace_Dark_Servant(resummon='True').execute()
        self.castedTime = time.time()
        while not bot_status.elite_boss_detected:
            Shadow_Attack().execute()
            if time.time() - self.castedTime > 5:
                break
        return True


class Burst(Command):
    def main(self, wait=True):
        p = bot_status.player_pos
        plat = shared_map.platform_of_point(p)
        assert (plat)
        Direction("left" if p.x - plat.begin_x > plat.end_x - p.x else "right").execute()
        Shadow_Bite().execute()
        Silence().execute()
        Quintuple_Star().execute()
        Rapid_Throw().execute()
        Quintuple_Star().execute()
        self.castedTime = time.time()
        return True


class Detect_Mobs(Command):
    def __init__(self, count=1):
        super().__init__(locals())
        self.count = int(count)

    def main(self, wait=True):
        if bot_helper.check_blind():
            # chat_bot.send_message("blind", capture.frame)
            if Cygnus_Knights_Will.canUse():
                Cygnus_Knights_Will().execute()
            elif Will_of_Erda.canUse():
                Will_of_Erda().execute()

        start = time.time()
        need_act = bot_status.stage_fright and gui_setting.auto.action and random() < 0.1
        mobs_count = -1
        while True:
            if capture.frame is None:
                time.sleep(0.1)
            else:
                mobs = detect_mobs(
                    capture.frame,
                    multy_match=self.count > 1,
                    debug=False)
                if mobs_count != len(mobs):
                    mobs_count = len(mobs)
                    utils.log_event(f"mobs count = {mobs_count}", bot_settings.debug)
                if mobs_count >= self.count or bot_status.elite_boss_detected:
                    break
                if time.time() - start >= 7:
                    utils.log_event("Detect_Mobs timeout", bot_settings.debug)
                    bot_status.prepared = False
                    break
                if need_act:
                    Random_Action().execute()
                    need_act = False
                else:
                    time.sleep(0.1)
        return True

###################
#      Buffs      #
###################


class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            Dark_Elemental,
            HEXA_Shadow_Bat,
            Transcendent_Cygnus_Blessing,
            LastResort,
            Glory_of_the_Guardians,
            Shadow_Spear,
            # Shadow_Illusion,
            ForTheGuild,
            HardHitter,
            Darkness_Ascending
        ]

        ForTheGuild.key = Keybindings.FOR_THE_GUILD
        HardHitter.key = Keybindings.HARD_HITTER
        LastResort.key = Keybindings.LAST_RESORT

        Arachnid.key = Keybindings.ARACHNID
        SolarCrest.key = Keybindings.SolarCrest

    def main(self, wait=True):
        for buff in self.buffs:
            if buff.canUse():
                # utils.log_event(str(buff), bot_settings.debug)
                result = buff().main(wait)
                if result:
                    return True
        return False


class Transcendent_Cygnus_Blessing(Skill):
    key = Keybindings.Transcendent_Cygnus_Blessing
    type = SkillType.Buff
    cooldown = 240
    precast = 0.3
    backswing = 0.85

    @classmethod
    def load(cls):
        module_name = cls.__module__.split('.')[-1]
        path1 = f'assets/skills/{module_name}/{cls.__name__}.png'
        cls.icon = cv2.imread(path1, 0)
        cls.id = cls.__name__

    @classmethod
    def check(cls):
        if capture.frame is None:
            return
        cls.check_buff_enabled()
        if cls.enabled:
            cls.ready = False
        else:
            matchs = utils.multi_match(
                capture.skill_frame, cls.icon[2:-2, 8:-2], threshold=0.9, debug=False)
            cls.ready = len(matchs) > 0

    @classmethod
    def check_buff_enabled(cls):
        matchs = utils.multi_match(
            capture.buff_frame, cls.icon[:14, 8:-8], threshold=0.9)
        if not matchs:
            matchs = utils.multi_match(
                capture.buff_frame, cls.icon[-14:, 8:-8], threshold=0.9)
        cls.enabled = len(matchs) > 0


class Glory_of_the_Guardians(Skill):
    key = Keybindings.Glory_of_the_Guardians
    type = SkillType.Buff
    cooldown = 120
    backswing = 0.75


class Shadow_Spear(Skill):
    key = Keybindings.Shadow_Spear
    type = SkillType.Buff
    cooldown = 177
    backswing = 0.6


class Shadow_Illusion(Skill):
    key = Keybindings.Shadow_Illusion
    type = SkillType.Buff
    cooldown = 180
    backswing = 0.75


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
        target_range = range(max(platform_target.begin_x - max_distance, platform_start.begin_x), platform_start.end_x + 1)
    else:
        target_range = range(platform_start.begin_x, min(platform_target.end_x + max_distance, platform_start.end_x) + 1)
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
    if gap <= -3:
        # 有交集
        # 优先垂直方向接近
        next_p = MapPoint(start.x, platform_target.y, 2)
        if target_reached(next_p, target):
            return next_p
        if shared_map.is_continuous(next_p, target):
            return target

        # 尝试水平方向接近
        next_p = MapPoint(target.x, start.y, 2)
        if not shared_map.is_continuous(start, next_p):
            next_p = None
        if next_p:
            if target_reached(start, next_p):
                return target
            else:
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
                return MapPoint(start.x, platform_target.y, 3)
            else:
                next_p = point_of_intersection(platform_start, platform_target)
                assert next_p
                if target_reached(start, next_p):
                    next_p.tolerance = 0
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

class Test_Command(Command):
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    backswing = 0.1

    def main(self, wait=True):
        for _ in range(0, 3):
            print('start:' + str(bot_status.player_pos.tuple))
            direction = 'right'
            key_down(direction)
            time.sleep(0.02)

            # 三段跳 40-41
            # press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.15)
            # press_acc(self.key, 2, down_time=0.1, up_time=0.03)

            # 二段跳 26-29
            # press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            # press(self.key, 1, down_time=0.02, up_time=0.02)

            # 急停
            # 23-25
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.2)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.2)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.1)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)

            # press(Keybindings.Quintu
            # ple_Star, down_time=0.01, up_time=0.02)

            # 26-27
            # press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            # press(self.key, 1, down_time=0.02, up_time=0.1)

            # 32-33
            # press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            # press(self.key, 2, down_time=0.02, up_time=0.1)

            # 40-42
            press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            press(self.key, 1, down_time=0.1, up_time=0.1)
            press(self.key, 1, down_time=0.02, up_time=0.2)

            # 44-46
            # press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            # press(self.key, 1, down_time=0.1, up_time=0.2)
            # press(self.key, 1, down_time=0.02, up_time=0.2)

            Shadow_Dodge('right').execute()

            key_up(direction)
            sleep_in_the_air(n=1)
            print('end: ' + str(bot_status.player_pos.tuple))
        return True

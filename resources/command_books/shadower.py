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
    if abs(d_x) in ShadowAssault.x_range and -d_y in ShadowAssault.y_range:
        if ShadowAssault.canUse():
            ShadowAssault(target=target).execute()
            return
    if d_y in ShadowAssault.y_range:
        if ShadowAssault.canUse():
            ShadowAssault(target=target).execute()
            return
    if abs(d_x) >= 26:
        hit_and_run('right' if d_x > 0 else 'left', target, tolerance)
        return

    next_p = find_next_point(bot_status.player_pos, target, tolerance)
    if not next_p:
        return

    bot_status.path = [bot_status.player_pos, next_p, target]

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
        hit_and_run(direction, next_p, tolerance)
    # elif abs(d_x) >= 20:
    #     DoubleJump(next_p).execute()
    else:
        Walk(target_x=next_p[0], tolerance=tolerance).execute()


@bot_status.run_if_enabled
def hit_and_run(direction, target, tolerance):
    if gui_setting.detection.detect_mob:
        if gui_setting.detection.detect_elite or gui_setting.detection.detect_boss:
            t = AsyncTask(target=pre_detect, args=(direction,))
            t.start()
            elite_detected = t.join()
            DoubleJump(target=target, attack_if_needed=True).execute()
            if elite_detected:
                SonicBlow().execute()
        else:
            DoubleJump(target=target, attack_if_needed=True).execute()
    else:
        DoubleJump(target=target, attack_if_needed=True).execute()

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
    elif dy <= 23:
        JumpUp(target).execute()
    elif dy <= 41 and ShadowAssault.canUse():
        ShadowAssault(target=target).execute()
    else:
        RopeLift(dy).execute()


@bot_status.run_if_enabled
def move_down(target):
    p = bot_status.player_pos
    dy = p[1] - target[1]
    if dy >= 24 and ShadowAssault.canUse():
        ShadowAssault(target=target).execute()
    else:
        sleep_in_the_air(n=1)
        if target[1] > bot_status.player_pos[1]:
            Fall().execute()


class JumpUp(Command):
    key = Keybindings.FLASH_JUMP
    type = SkillType.Move

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
        press(self.key, 1)
        key_up('up')
        sleep_in_the_air()


class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.FLASH_JUMP
    type = SkillType.Move
    # cooldown = 0.1

    def __init__(self, target: tuple[int, int], attack_if_needed=False):
        super().__init__(locals())

        self.target = target
        self.attack_if_needed = attack_if_needed

    def detect_mob(self, direction):
        insets = AreaInsets(top=220,
                            bottom=100,
                            left=650 if direction == 'left' else 10,
                            right=10 if direction == 'left' else 600)
        anchor = capture.locate_player_fullscreen(accurate=True)
        mobs = detect_mobs(insets=insets, anchor=anchor)
        return mobs

    def main(self):
        while not self.canUse():
            time.sleep(0.01)
        dx = self.target[0] - bot_status.player_pos[0]
        dy = self.target[1] - bot_status.player_pos[1]
        direction = 'left' if dx < 0 else 'right'
        start_y = bot_status.player_pos[1]

        self.__class__.castedTime = time.time()
        key_down(direction)
        if self.attack_if_needed:
            # detect = AsyncTask(
            #     target=self.detect_mob, args=(direction, ))
            # detect.start()
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.05)
            # mobs_detected = detect.join()
            mobs_detected = True
            times = 2 if mobs_detected else 1
            press(self.key, 1, down_time=0.03, up_time=0.03)
            if mobs_detected:
                Attack().execute()
        else:
            times = 2 if abs(dx) >= 32 else 1
            if dy == 0:
                if abs(dx) in range(20, 26):
                    press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.2)
                else:
                    press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
            else:
                press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.05)
            press(self.key, times, down_time=0.03, up_time=0.03)

        key_up(direction)
        sleep_in_the_air(n=2, start_y=start_y)


class ShadowAssault(Skill):
    """
    ShadowAssault in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """
    id = 'ShadowAssault'
    key = Keybindings.SHADOW_ASSAULT
    type = SkillType.Move
    backswing = 0.3
    max_times = 4
    usable_times = 4
    cooldown = 60
    x_range = range(18, 36)
    y_range = range(18, 42)

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
            if dy < 0 and abs(dx) >= 16:
                self.direction = 'upright' if dx > 0 else 'upleft'
                self.jump = True
            elif dy > 0 and abs(dx) >= 16:
                self.direction = 'downright' if dx > 0 else 'downleft'
                self.jump = True
            elif dy == 0:
                self.direction = 'left' if dx < 0 else 'right'
                self.jump = False
            else:
                self.direction = 'up' if dy < 0 else 'down'
                self.jump = True
            self.distance = math.sqrt(dx ** 2 + dy ** 2)

    @classmethod
    def check(cls):
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[10:-2, 2:-16], threshold=0.98, debug=False)
        if matchs:
            cls.ready = True
            cls.usable_times = cls.max_times
        else:
            matchs = utils.multi_match(
                capture.buff_frame, cls.icon[2:-2, 2:-16], threshold=0.9)
            cls.ready = len(matchs) > 0
            if not cls.ready:
                cls.usable_times = 0

    def main(self):
        if self.distance == 0:
            return

        if not self.canUse():
            return

        # time.sleep(0.2)

        if self.direction.endswith('left'):
            if bot_status.player_direction != 'left':
                press('left', down_time=0.1)
        elif self.direction.endswith("right"):
            if bot_status.player_direction != 'right':
                press("right", down_time=0.1)
        elif self.direction == 'up' or self.direction == 'down':
            time.sleep(0.2)
            evade_rope(self.target)
            
        if self.direction == 'up' and not map.on_the_platform((bot_status.player_pos[0], self.target[1])):
            Walk(target_x=self.target[0], tolerance=0).execute()

        if self.jump:
            if self.direction.startswith('down'):
                key_down('down')
                press(Keybindings.JUMP, 1, down_time=0.2, up_time=0.2)
                key_up("down")
            else:
                press(Keybindings.JUMP)
                dy = self.target[1] - bot_status.player_pos[1]
                time.sleep(0.1 if abs(dy) > 32 else 0.4)

        key_down(self.direction)
        time.sleep(0.03)

        self.__class__.usable_times -= 1
        press(self.key)
        key_up(self.direction)
        sleep_in_the_air()
        time.sleep(self.backswing)
        MesoExplosion().execute()
        
        # if bot_settings.record_layout:
        #     layout.add(*bot_status.player_pos)


#########################
#         Skills        #
#########################

class Attack(Command):
    key = Keybindings.CRUEL_STAB
    type = SkillType.Attack
    backswing = 0.1

    def main(self):
        CruelStab().execute()

class Aoe(Skill):
    key = Keybindings.TRICKBLADE
    type = SkillType.Attack
    
    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return TrickBlade.ready
    
    def main(self):
        return TrickBlade().main()

class CruelStab(Skill):
    """Uses 'CruelStab' once."""
    key = Keybindings.CRUEL_STAB
    type = SkillType.Attack
    # cooldown = 0.5
    backswing = 0.1

    def main(self):
        if not self.canUse():
            return
        self.__class__.castedTime = time.time()
        jumped = not map.on_the_platform(bot_status.player_pos)
        press(self.key, 1, up_time=0.3)
        MesoExplosion().execute()
        time.sleep(0.5 if not jumped else self.backswing)


class MesoExplosion(Skill):
    """Uses 'MesoExplosion' once."""
    key = Keybindings.MESO_EXPLOSION
    type = SkillType.Attack

    def main(self):
        press(self.key, down_time=0.01, up_time=0.01)


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

    def main(self):
        if self.direction is not None:
            press_acc(self.direction, down_time=0.03, up_time=0.03)
        super().main()


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

    def main(self):
        if self.direction is not None:
            press(self.direction)
        super().main()


class SuddenRaid(Skill):
    key = Keybindings.SUDDEN_RAID
    cooldown = 30
    backswing = 0.75
    type = SkillType.Attack

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        usable = super().canUse()
        if usable:
            mobs = detect_mobs()
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

    # def __init__(self, direction='right'):
    #     super().__init__(locals())
    #     if direction is None:
    #         self.direction = direction
    #     else:
    #         self.direction = bot_settings.validate_horizontal_arrows(direction)

    # @classmethod
    # def canUse(cls, next_t: float = 0) -> bool:
    #     usable = super().canUse()
    #     if usable:
    #         mobs = detect_mobs(insets=AreaInsets(
    #             top=200, bottom=150, left=400, right=400))
    #         return len(mobs) > 0
    #     else:
    #         return False


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


###################
#      Buffs      #
###################


class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs: list[Skill] = [
            MapleWarrior,
            MapleWorldGoddessBlessing,
            LastResort,
            ForTheGuild,
            HardHitter,
            ShadowWalker,
            PickPocket,
        ]

    def main(self):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!use buff")
        for buff in self.buffs:
            if buff.canUse():
                print(buff)
                result = buff().execute()
                if result:
                    break


class ShadowWalker(Skill):
    key = Keybindings.SHADOW_WALKER
    cooldown = 180
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff

    def main(self):
        super().main()
        # bot_status.hide_start = time.time()


class EPIC_ADVENTURE(Skill):
    key = Keybindings.EPIC_ADVENTURE
    cooldown = 120
    backswing = 0.75
    type = SkillType.Buff

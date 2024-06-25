"""A collection of classes used to execute a Routine."""

import time
from src.command import commands
from src.common import bot_settings, bot_status, bot_helper
from src.common.vkeys import *
from src.common.constants import *


class Component:
    id = 'Routine Component'
    PRIMITIVES = {int, str, bool, float}
    complete_callback = None

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError(
                'Component superclass __init__ only accepts 1 (optional) argument: LOCALS')
        if len(kwargs) != 0:
            raise TypeError(
                'Component superclass __init__ does not accept any keyword arguments')
        if len(args) == 0:
            self.kwargs = {}
        elif type(args[0]) != dict:
            raise TypeError(
                "Component superclass __init__ only accepts arguments of type 'dict'.")
        else:
            self.kwargs = args[0].copy()
            self.kwargs.pop('__class__')
            self.kwargs.pop('self')

    @bot_status.run_if_enabled
    def execute(self):
        self.main()
        # print(str(self))

    def main(self):
        pass

    def update(self, *args, **kwargs):
        """Updates this Component's constructor arguments with new arguments."""

        # Validate arguments before actually updating values
        self.__class__(*args, **kwargs)
        self.__init__(*args, **kwargs)

    def info(self):
        """Returns a dictionary of useful information about this Component."""

        return {
            'name': self.__class__.__name__,
            'vars': self.kwargs.copy()
        }

    def encode(self):
        """Encodes an object using its ID and its __init__ arguments."""

        arr = [self.id]
        for key, value in self.kwargs.items():
            if key != 'id' and type(self.kwargs[key]) in Component.PRIMITIVES:
                arr.append(f'{key}={value}')
        return ', '.join(arr)


#################################
#       Routine Components      #
#################################

class Label(Component):
    id = '@'

    def __init__(self, label):
        super().__init__(locals())
        self.label = str(label)
        self.index = None

    def _main(self):
        for component in self.series:
            component.execute()

    def set_index(self, i):
        self.index = i

    def encode(self):
        return '\n' + super().encode()

    def info(self):
        curr = super().info()
        curr['vars']['index'] = self.index
        return curr

    def __str__(self):
        return f'{self.id}{self.label}:'


class Point(Component):
    """Represents a location in a user-defined routine."""

    id = '*'

    def __init__(self, x, y, interval=0, tolerance=13, detect="False", skip="False") -> None:
        super().__init__(locals())
        self.x = int(x)
        self.y = int(y)
        self.location = (self.x, self.y)
        self.interval = bot_settings.validate_nonnegative_int(interval)
        self.tolerance = int(tolerance)
        self.detect = bot_settings.validate_boolean(detect)
        self.skip = bot_settings.validate_boolean(skip)
        self.last_execute_time = 0
        self.parent: Component | None = None
        self.index = 0
        if not hasattr(self, 'commands'):       # Updating Point should not clear commands
            self.commands: list[commands.Command] = []

    def main(self):
        """Executes the set of actions associated with this Point."""
        # self.print_debug_info()

        if self.skip and self.last_execute_time == 0:
            self.last_execute_time = time.time()
            return
        if self.interval > 0:
            if time.time() - self.last_execute_time >= self.interval:
                self._main()
        else:
            self._main()

    def _main(self):
        self.pre_move()
        commands.Move(self.x, self.y, self.tolerance).execute()
        for command in self.commands:
            command.execute()
        self.last_execute_time = time.time()
        if Component.complete_callback:
            Component.complete_callback(self)

    def pre_move(self):
        d_x = self.x - bot_status.player_pos.x
        d_y = self.y - bot_status.player_pos.y
        if d_x != 0:
            direction = 'right' if d_x > 0 else 'left'
            key_down(direction)
            time.sleep(0.05)
            key_up(direction)
        else:
            direction = bot_status.player_direction
        if self.detect and bot_status.player_pos.y == self.y:
            self.detect_mob(direction)

    def detect_mob(self, direction):
        start_time = time.time()
        anchor = bot_helper.locate_player_fullscreen(accurate=True)
        # matchs = commands.detect_mobs(insets=commands.AreaInsets(top=250, bottom=100, left=300, right=300),
        #                               anchor=anchor)
        # if matchs:
        #     print("use aoe")
        #     commands.Aoe().execute()
        cast_time = time.time() - start_time
        time.sleep(max(1 - cast_time, 0))

        start_time = time.time()
        while True:
            anchor = bot_helper.locate_player_fullscreen(accurate=True)
            # matchs = []
            # if gui_setting.detection.detect_boss:
            #     matchs = commands.detect_mobs(insets=commands.AreaInsets(top=180, bottom=-20, left=300, right=300),
            #                                   anchor=anchor,
            #                                   type=commands.MobType.BOSS)
            # if not matchs and gui_setting.detection.detect_elite:
            #     matchs = commands.detect_mobs(insets=commands.AreaInsets(top=180, bottom=-20, left=300, right=300),
            #                                   anchor=anchor,
            #                                   type=commands.MobType.ELITE)
            # if matchs:
                # SonicBlow().execute()
            mobs = bot_helper.detect_mobs_around_anchor(
                insets=AreaInsets(top=350, bottom=100, left=1200 if direction == 'left' else -300, right=1100 if direction == 'right' else -300),
                anchor=anchor,
                multy_match=True,
                debug=False
            )

            if len(mobs):
                print(f"mobs count = {len(mobs)}")
            if len(mobs) > 1:
                break
            if time.time() - start_time > 6:
                break

            time.sleep(0.001)

    def info(self):
        curr = super().info()
        curr['vars'].pop('location', None)
        curr['vars']['commands'] = ', '.join([c.id for c in self.commands])
        return curr

    def __str__(self):
        return f'  * {self.location}'


class Sequence(Component):
    """A series of actions."""

    id = '~'

    def __init__(self, label, interval=0, skip='False'):
        super().__init__(locals())
        self.label = str(label)
        self.interval = bot_settings.validate_nonnegative_int(interval)
        self.skip = bot_settings.validate_boolean(skip)

        self.last_execute_time = 0
        self.path: list[Point] = []
        self.index = None

    def main(self):
        """Executes the series of actions associated with this Sequence."""

        if self.interval > 0:
            now = time.time()
            if self.skip and self.last_execute_time == 0:
                self.last_execute_time = now
            if now - self.last_execute_time >= self.interval:
                self._main()
        else:
            self._main()

    def _main(self):
        for point in self.path:
            point.execute()
        self.last_execute_time = time.time()
        if Component.complete_callback:
            Component.complete_callback(self)

    def add_component(self, component: Point):
        component.parent = self
        component.index = len(self.path)
        self.path.append(component)

    def set_index(self, i):
        self.index = i

    def encode(self):
        return '\n' + super().encode()

    def info(self):
        curr = super().info()
        curr['vars']['index'] = self.index
        # curr['vars']['series'] = self.series
        return curr

    def __delete__(self, instance):
        pass
        # del self.series
        # routine.labels.pop(self.label)

    def __str__(self):
        return f'{self.id}{self.label}:'


class Setting(Component):
    """Changes the value of the given setting variable."""

    id = '$'

    def __init__(self, target, value):
        super().__init__(locals())
        self.key = str(target)
        if self.key not in bot_settings.SETTING_VALIDATORS:
            raise ValueError(f"Setting '{target}' does not exist")
        self.value = bot_settings.SETTING_VALIDATORS[self.key](value)

    def main(self):
        setattr(bot_settings, self.key, self.value)

    def __str__(self):
        return f'  $ {self.key} = {self.value}'


class End(Component):
    id = '#'

    def __str__(self):
        return self.id


SYMBOLS = {
    '*': Point,
    '@': Label,
    '$': Setting,
    '~': Sequence,
    '#': End,
}

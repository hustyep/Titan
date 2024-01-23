"""A collection of classes used in the 'machine code' generated by Mars's compiler for each routine."""

import csv
import os
from os.path import splitext, basename
from enum import Enum
from rx.subject import Subject

from src.rune import rune
from src.common.constants import *
from src.common import bot_settings, utils
from src.routine.components import *
from src.command.commands import Command, target_reached, Move
from src.map.map import map
from src.command.command_book import CommandBook
from src.common.action_simulator import *


class RoutineUpdateType(Enum):
    loaded = 'routine_loaded'
    cleared = 'routine_cleared'
    updated = 'routine_updated'
    selected = 'routine_selected'


def update(func):
    """
    Decorator function that updates both the displayed routine and details
    for all mutative Routine operations.
    """

    def f(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.on_next((RoutineUpdateType.updated, ))
        return result
    return f


def dirty(func):
    """Decorator function that sets the dirty bit for mutative Routine operations."""

    def f(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.dirty = True
        return result
    return f


class Routine(Subject):
    """Describes a routine file in Mars's custom 'machine code'."""

    def __init__(self):
        super().__init__()
        self.dirty = False
        self.path = ''
        self.labels = {}
        self.index = 0
        self.sequence: list[Component] = []
        self.display = []       # Updated alongside sequence
        self.command_book = None
        self.settings: list[Setting] = []

    @dirty
    @update
    def set(self, arr):
        self.sequence = arr
        self.display = [str(x) for x in arr]

    @dirty
    @update
    def append_component(self, p: Component):
        self.sequence.append(p)
        self.display.append(str(p))

    @dirty
    @update
    def append_command(self, i, c: Command):
        """Appends Command object C to the Point at index I in the sequence."""

        target = self.sequence[i]
        if isinstance(target, Point):
            target.commands.append(c)
        else:
            raise ValueError(f"{str(target)} at index {i} is not a Point")

    @dirty
    @update
    def move_component_up(self, i):
        """Moves the component at index I upward if possible."""

        if i > 0:
            temp_s = self.sequence[i-1]
            temp_d = self.display[i-1]
            self.sequence[i-1] = self.sequence[i]
            self.display[i-1] = self.display[i]
            self.sequence[i] = temp_s
            self.display[i] = temp_d
            return i - 1
        return i

    @dirty
    @update
    def move_component_down(self, i):
        if i < len(self.sequence) - 1:
            temp_s = self.sequence[i+1]
            temp_d = self.display[i+1]
            self.sequence[i+1] = self.sequence[i]
            self.display[i+1] = self.display[i]
            self.sequence[i] = temp_s
            self.display[i] = temp_d
            return i + 1
        return i

    @dirty
    @update
    def move_command_up(self, i, j):
        """
        Within the Point at routine index I, moves the Command at index J upward
        if possible and updates the Edit UI.
        """

        point = self.sequence[i]
        if j > 0:
            temp = point.commands[j-1]
            point.commands[j-1] = point.commands[j]
            point.commands[j] = temp
            return j - 1
        return j

    @dirty
    @update
    def move_command_down(self, i, j):
        point = self.sequence[i]
        if j < len(point.commands) - 1:
            temp = point.commands[j+1]
            point.commands[j+1] = point.commands[j]
            point.commands[j] = temp
            return j + 1
        return j

    @dirty
    @update
    def delete_component(self, i):
        """Deletes the Component at index I."""

        self.sequence.pop(i)
        self.display.pop(i)

    @dirty
    @update
    def delete_command(self, i, j):
        """Within the Point at routine index I, deletes the Command at index J."""

        point = self.sequence[i]
        point.commands.pop(j)

    @update
    def update_component(self, i, new_kwargs):
        target = self.sequence[i]
        try:
            target.update(**new_kwargs)
            self.display[i] = str(target)
            self.dirty = True
        except (ValueError, TypeError) as e:
            print(
                f"\n[!] Found invalid arguments for '{target.__class__.__name__}':")
            print(f"{' ' * 4} -  {e}")

    @update
    def update_command(self, i, j, new_kwargs):
        target = self.sequence[i].commands[j]
        try:
            target.update(**new_kwargs)
            self.display[i] = str(self.sequence[i])
            self.dirty = True
        except (ValueError, TypeError) as e:
            print(
                f"\n[!] Found invalid arguments for '{target.__class__.__name__}':")
            print(f"{' ' * 4} -  {e}")

    def current_step(self):
        return self.sequence[self.index]

    @bot_status.run_if_enabled
    def step(self):
        """Increments config.seq_index and wraps back to 0 at the end of config.sequence."""
        self._run()
        add = 1
        element = self.current_step()
        if isinstance(element, Sequence):
            add += len(element.path)
        elif isinstance(element, Point) and element.parent:
            add = add - element.index - 2 + len(element.parent.path)
        self.index = (self.index + add) % len(self.sequence)

    def save(self, file_path=None):
        """Encodes and saves the current Routine at location PATH."""
        if not file_path:
            file_path = self.path

        result = []
        for item in self.sequence:
            result.append(item.encode())
            if isinstance(item, Point):
                for c in item.commands:
                    result.append(' ' * 4 + c.encode())
        result.append('')

        with open(file_path, 'w') as file:
            file.write('\n'.join(result))
        self.dirty = False

        utils.print_separator()
        print(f"[~] Saved routine to '{basename(file_path)}'.")

    def clear(self):
        self.index = 0
        self.set([])
        self.dirty = False
        self.path = ''
        self.labels = {}
        self.command_book = None
        map.clear()
        bot_settings.reset()

        self.on_next((RoutineUpdateType.cleared, ))

    def load(self, file: str, command_book: CommandBook = None):
        """
        Attempts to load FILE into a sequence of Components. If no file path is provided, attempts to
        load the previous routine file.
        :param file:    The file's path.
        :return:        None
        """
        if command_book is None:
            if self.command_book is None:
                raise ValueError(" ! No Command Book")
            else:
                command_book = self.command_book

        map_name = basename(splitext(file)[0])
        utils.print_separator()
        print(f"[~] Loading routine '{map_name}':")

        if not file or not os.path.exists(file):
            print('[!] File path not provided, try load default routine')
            file = os.path.join(bot_settings.get_routines_dir(), 'default.csv')
            if not os.path.exists(file):
                print('[!] default routine not provided')
                return False

        ext = splitext(file)[1]
        if ext != '.csv':
            print(f" !  '{ext}' is not a supported file extension.")
            return False

        self.clear()
        self.command_book = command_book
        Command.loop_begin_callback = self._on_loop_begin
        Command.complete_callback = self._on_command_complete
        Component.complete_callback = self._on_component_complete

        # Compile and Link
        self.compile(file)
        map.load_data(map_name)

        self.dirty = False
        self.path = file

        self.on_next((RoutineUpdateType.loaded, ))
        print(f" ~  Finished loading routine '{map_name}'.")

    def compile(self, file):
        self.labels = {}
        with open(file, newline='') as f:
            csv_reader = csv.reader(f, skipinitialspace=True)
            curr_point: Point = None
            curr_sequence: Sequence = None
            line = 1
            for row in csv_reader:
                result = self._eval(row, line)
                if result:
                    if isinstance(result, Command):
                        if curr_point:
                            curr_point.commands.append(result)
                    elif isinstance(result, Sequence):
                        curr_sequence = result
                        self.append_component(result)
                    elif isinstance(result, Point):
                        curr_point = result
                        if curr_sequence:
                            curr_sequence.add_component(result)
                        self.append_component(result)
                        self.update_boundary_point(result)
                    elif isinstance(result, End):
                        curr_sequence = None
                        self.append_component(result)
                    else:
                        self.append_component(result)
                line += 1

    def _eval(self, row, i):
        if row and isinstance(row, list):
            first, rest = row[0].lower(), row[1:]
            args, kwargs = utils.separate_args(rest)
            line_error = f' !  Line {i}: '

            if first in SYMBOLS:
                c = SYMBOLS[first]
            elif first in self.command_book:
                c = self.command_book[first]
            else:
                print(line_error + f"Command '{first}' does not exist.")
                return

            try:
                obj = c(*args, **kwargs)
                if isinstance(obj, Label):
                    obj.set_index(len(self))
                    self.labels[obj.label] = obj
                elif isinstance(obj, Setting):
                    self.settings.append(obj)
                    obj.main()
                return obj
            except (ValueError, TypeError) as e:
                print(line_error +
                      f"Found invalid arguments for '{c.__name__}':")
                print(f"{' ' * 4} -  {e}")

    def update_boundary_point(self, point: Point):
        if point.location[0] < bot_settings.boundary_point_l[0]:
            bot_settings.boundary_point_l = point.location
        elif point.location[0] > bot_settings.boundary_point_r[0]:
            bot_settings.boundary_point_r = point.location

    def get_all_components(self):
        """Returns a dictionary mapping all creatable Components to their names."""

        options = self.command_book.dict.copy()
        for e in (Point, Label, Sequence, Setting, End):
            options[e.__name__.lower()] = e
        return options

    def __getitem__(self, i):
        return self.sequence[i]

    def __len__(self):
        return len(self.sequence)

    @bot_status.run_if_enabled
    def _run(self):
        # current element
        element = self.current_step()

        # Highlight the current Point
        self.on_next((RoutineUpdateType.selected, element))
        
        if isinstance(element, Point):
            # new_direction = 'right' if element.location[0] > bot_status.player_pos[0] else 'left'
            # if new_direction == bot_status.player_direction:
            pass

        # Execute next Point in the routine
        element.execute()

    def _on_loop_begin(self):
        pass
        # Feed Pet
        # self.command_book.FeedPet().execute()
        # Use Buff and Potion
        # self.command_book.Potion().execute()
        # self.command_book.Buff().execute()

    def _on_command_complete(self, c: Command):
        if isinstance(c, Move) and not target_reached(bot_status.player_pos, c.target, tolerance=c.tolerance):
            self.check_point(bot_status.player_pos)
            
    def _on_component_complete(self, c: Component):
        if isinstance(c, Point):
            self.check_point(c.location)

    @bot_status.run_if_enabled
    def check_point(self, p):
        if bot_status.point_checking:
            return
        bot_status.point_checking = True
        if bot_status.rune_pos is not None:
            result, frame = self.command_book.SolveRune(
                bot_status.rune_pos).execute()
            threading.Thread(target=self.solve_rune_callback,
                             args=(result, frame)).start()
        if bot_status.minal_pos \
                and (utils.distance(p, bot_status.minal_pos) <= 25 or p == bot_status.minal_closest_pos):
            self.command_book.Mining(bot_status.minal_pos).execute()
        bot_status.point_checking = False

    def solve_rune_callback(self, result, frame):
        if result == 1:
            self.check_rune_solve_result(frame)
        elif result == 0:
            self.on_next((BotWarnning.RUNE_INTERACT_FAILED, ))
        elif result == -1 and frame is not None:
            self.notify_rune_failed(frame)

    def check_rune_solve_result(self, used_frame):
        for _ in range(4):
            rune_type = rune.rune_liberate_result(capture.frame)
            if rune_type is not None:
                break
            time.sleep(0.1)
        if rune_type is None:
            self.notify_rune_failed(used_frame)
        else:
            self.on_next((BotInfo.RUNE_LIBERATED, rune_type))
            if rune_type == 'Rune of Might':
                ActionSimulator.cancel_rune_buff()

    def notify_rune_failed(self, used_frame):
        bot_status.rune_pos = None
        bot_status.rune_closest_pos = None
        self.on_next((BotWarnning.RUNE_FAILED, ))
        file_path = 'screenshot/rune_failed'
        utils.save_screenshot(
            frame=used_frame, file_path=file_path, compress=False)


routine = Routine()

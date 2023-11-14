import os
import inspect
import importlib
import traceback
from os.path import basename, splitext
from src.common import bot_settings, utils
from src.command import commands

CB_KEYBINDING_DIR = os.path.join('resources', 'keybindings')


class CommandBook():
    def __init__(self, file):
        self.name = splitext(basename(file))[0]
        self.Move = commands.Move
        self.Walk = commands.Walk
        self.Wait = commands.Wait
        self.ErdaShower = commands.ErdaShower
        self.SolveRune = commands.SolveRune
        self.Mining = commands.Mining
        self.FeedPet = commands.FeedPet

        self.Summon = commands.Summon
        self.DotAoe = commands.DotAoe
        self.Buff = commands.Buff
        self.Potion = commands.Potion

        self.step = commands.step

        result = self._load_commands(file)
        if result is None:
            raise ValueError(f"Invalid command book at '{file}'")
        self.dict, self.module = result
        bot_settings.class_name = self.name

    def _load_commands(self, file):
        """Prompts the user to select a command module to import. Updates config's command book."""

        utils.print_separator()
        print(f"[~] Loading command book '{basename(file)}':")

        ext = splitext(file)[1]
        if ext != '.py':
            print(f" !  '{ext}' is not a supported file extension.")
            return

        # Import the desired command book file
        target = '.'.join(['resources', 'command_books', self.name])
        try:
            module = importlib.import_module(target)
            module = importlib.reload(module)
        except ImportError:     # Display errors in the target Command Book
            print(' !  Errors during compilation:\n')
            for line in traceback.format_exc().split('\n'):
                line = line.rstrip()
                if line:
                    print(' ' * 4 + line)
            print(f"\n !  Command book '{self.name}' was not loaded")
            return

        new_func = {}
        new_cb = {}
        # load default Fuction
        for name, func in inspect.getmembers(commands, inspect.isfunction):
            new_func[name.lower()] = func

        # load default Command
        for name, command in inspect.getmembers(commands, inspect.isclass):
            if issubclass(command, commands.Command):
                new_cb[name.lower()] = command

        # Populate the new command book
        for name, func in inspect.getmembers(module, inspect.isfunction):
            new_func[name.lower()] = func

        for name, command in inspect.getmembers(module, inspect.isclass):
            if issubclass(command, commands.Command):
                new_cb[name.lower()] = command

        # Load key map
        if hasattr(module, 'Keybindings'):
            commands.Keybindings = module.Keybindings
        else:
            print(
                f" !  Error loading command book '{self.name}', keymap class 'Keybindings' is missing")
            return

        # Check if required functions have been implemented and overridden
        required_function_found = True
        for func_name in ['step']:
            if func_name not in new_func:
                required_function_found = False
                print(
                    f" !  Error: Must implement required function '{func_name}'.")

        # Check if required commands have been implemented and overridden
        required_command_found = True
        for command in [commands.Buff, commands.Attack]:
            name = command.__name__.lower()
            if name not in new_cb:
                required_command_found = False
                new_cb[name] = command
                print(f" !  Error: Must implement required command '{name}'.")

        if required_command_found and required_function_found:
            self.Buff = new_cb['buff']
            # self.Potion = commands.Potion

            self.step = new_func['step']
            commands.step = self.step
            commands.Attack = new_cb["attack"]

            for command in (commands.Summon, commands.DotAoe):
                name = command.__name__
                if name.lower() in new_cb:
                    self.__setattr__(name, new_cb[name.lower()])
            print(f" ~  Successfully loaded command book '{self.name}'")
            return new_cb, module
        else:
            print(f" !  Command book '{self.name}' was not loaded")

    def __getitem__(self, item):
        return self.dict[item]

    def __contains__(self, item):
        return item in self.dict

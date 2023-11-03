import os
import inspect
import importlib
import traceback
from os.path import basename, splitext
from src.common import settings, utils
from command import commands

CB_KEYBINDING_DIR = os.path.join('resources', 'keybindings')


class CommandBook():
    def __init__(self, file):
        self.name = splitext(basename(file))[0]

        self.Move = commands.Move
        self.Walk = commands.Walk
        self.Wait = commands.Wait

        self.MoveVertical = commands.MoveVertical
        self.MoveHorizontal = commands.MoveHorizontal
        self.Buff = commands.Buff
        self.Potion = commands.Potion

        result = self._load_commands(file)
        if result is None:
            raise ValueError(f"Invalid command book at '{file}'")
        self.dict, self.module = result

    def _load_commands(self, file):
        """Prompts the user to select a command module to import. Updates config's command book."""

        utils.print_separator()
        print(f"[~] Loading command book '{basename(file)}':")

        ext = splitext(file)[1]
        if ext != '.py':
            print(f" !  '{ext}' is not a supported file extension.")
            return

        new_cb = {}

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

        # Load key map
        if hasattr(module, 'Keybindings'):
            default_config = {}
            for key, value in module.Keybindings.__dict__.items():
                if not key.startswith('__') and not key.endswith('__'):
                    default_config[key] = value
            self.DEFAULT_CONFIG = default_config
        else:
            print(
                f" !  Error loading command book '{self.name}', keymap class 'Keybindings' is missing")
            return

        # Populate the new command book
        for name, command in inspect.getmembers(module, inspect.isclass):
            if issubclass(command, commands.Command):
                new_cb[name.lower()] = command

        # Check if required commands have been implemented and overridden
        required_found = True
        for command in (commands.MoveVertical, commands.MoveHorizontal, commands.Buff, commands.Potion):
            name = command.__name__.lower()
            if name not in new_cb:
                required_found = False
                new_cb[name] = command
                print(f" !  Error: Must implement required command '{name}'.")

        if required_found:
            self.MoveVertical = new_cb['movevertical']
            self.MoveHorizontal = new_cb['movehorizontal']
            self.Buff = new_cb['buff']
            self.Potion = new_cb["potion"]

            print(f" ~  Successfully loaded command book '{self.name}'")
            return new_cb, module
        else:
            print(f" !  Command book '{self.name}' was not loaded")

    def __getitem__(self, item):
        return self.dict[item]

    def __contains__(self, item):
        return item in self.dict

    def load_config(self):
        super().load_config()
        self._set_keybinds()

    def save_config(self):
        self._set_keybinds()
        super().save_config()

    def _set_keybinds(self):
        for k, v in self.config.items():
            setattr(self.module.Keybindings, k, v)


command_book = CommandBook()

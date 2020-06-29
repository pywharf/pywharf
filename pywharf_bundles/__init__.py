from collections import defaultdict
import os
import sys
from typing import Callable, Dict

from pywharf_core.server import run_server_cli
from pywharf_core.workflow import update_index_cli
from pywharf_core.backend import BackendInstanceManager


def build_command_to_func() -> Dict[str, Callable[[], int]]:
    command_to_func = {
        'server': run_server_cli,
        'update_index': update_index_cli,
    }

    bim = BackendInstanceManager()
    for reg in bim._type_to_registration.values():  # pylint: disable=protected-access
        for name, func in reg.cli_name_to_func.items():
            command = reg.type.lower() + '.' + name.lower()
            command_to_func[command] = func

    return command_to_func


def run():
    command_to_func = build_command_to_func()

    help_supported_commands = '\n'.join(f'    {command}' for command in command_to_func)
    help_doc = f'''\
SYNOPSIS
    pywharf <command> <command_flags>

SUPPORTED COMMANDS
{help_supported_commands}
'''

    if len(sys.argv) < 2:
        print(help_doc)
        return 1

    command = sys.argv[1]
    if command not in command_to_func:
        print(help_doc)
        return 1

    # Shift argv left.
    sys.argv = sys.argv[1:]
    # Run.
    return command_to_func[command]()


def run_env():
    '''
    PYWHARF_COMMAND: to set <command>.
    PYWHARF_COMMAND_<FLAG>: to set <command_flags>.
    '''

    command = None
    command_flags = {}

    for key, val in os.environ.items():
        key = key.upper()
        if key == 'PYWHARF_COMMAND':
            command = val

        elif key.startswith('PYWHARF_COMMAND_'):
            flag = key[len('PYWHARF_COMMAND_'):].lower()
            assert flag
            command_flags[flag] = val

    if not command:
        raise RuntimeError('PYWHARF_COMMAND not set.')

    # Fill argv.
    argv = ['pywharf', command]
    for flag, val in command_flags.items():
        argv.append(f'--{flag}')
        if val:
            argv.append(val)

    sys.argv = argv
    return run()


def main():
    if len(sys.argv) <= 1:
        return run_env()
    else:
        return run()

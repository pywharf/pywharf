import sys
import os
import os.path
import stat
import toml
import fire

TEMPLATE = '''#!{python}
import sys
from importlib import import_module

if __name__ == '__main__':
    sys.exit(import_module('{module}').{func}())
'''


def build_script(command, module_func, output):
    module, func = module_func.split(':')
    script_content = TEMPLATE.format(python=sys.executable, module=module, func=func)

    with open(output, 'w') as fout:
        fout.write(script_content)
    os.chmod(output, os.stat(output).st_mode | stat.S_IEXEC)


def main(pyproject, output):
    with open(pyproject) as fin:
        config = toml.loads(fin.read())

    for command, module_func in config['tool']['poetry']['scripts'].items():
        script_path = os.path.join(output, command)
        print('Create', script_path)
        build_script(command, module_func, script_path)


fire.Fire(main)

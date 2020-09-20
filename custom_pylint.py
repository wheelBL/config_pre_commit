#!env python3
import re
import sys
from collections import OrderedDict
from enum import Enum
from itertools import filterfalse
from subprocess import PIPE, Popen
from sys import modules

print("[DEBUG]", sys.argv)
args = sys.argv
args[0] = "pylint"

proc = Popen(args, stdout=PIPE)
outs, errs = proc.communicate()
outs = outs.decode("UTF-8")
errs = errs.decode("UTF-8") if errs is not None else None

white_rules = [
    ("test.py"),
    ("custom_pylint.py", "missing-module-docstring"),
    ("custom_pylint.py", "missing-class-docstring"),
]

if proc.returncode == 0:
    sys.exit(0)


class State(Enum):
    header_module = 1
    line_error = 2


pattern_header_moudle = r"\*+ Module ([\w_]+)"
pattern_error = r"[\w_]+.py:\d+:\d+: (\w\d{4}): [^\n]+"


def get_state(string):
    res = re.match(pattern_header_moudle, string)
    if res:
        return State.header_module, res.group(0)
    res = re.match(pattern_error, string)
    if res:
        return State.line_error, res.group(0).strip()
    return None, None


def parse_output(outs):
    modules = OrderedDict()
    for line in outs.splitlines():
        state, context = get_state(line)
        if state == State.header_module:
            modules[context] = []
            current_module = context
        elif state == State.line_error:
            modules[current_module].append(context)
    return modules


def need_block(line, rules):
    return any(all(item in line for item in rule) for rule in rules)


info_modules = parse_output(outs)

blocks = OrderedDict()
for key in info_modules.copy():
    for line in info_modules[key][:]:
        if need_block(line, white_rules):
            blocks.setdefault(key, []).append(line)
            info_modules[key].remove(line)

    if not info_modules[key]:
        info_modules.pop(key)

if not info_modules:
    sys.exit(0)

print("\n######## remain #########")
for module in info_modules:
    print(module)
    for item in info_modules[module]:
        print(item)

print("\n######## block #########")
for module in blocks:
    print(module)
    for item in blocks[module]:
        print(item)

sys.exit(proc.returncode)

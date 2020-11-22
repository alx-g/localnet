import re
import sys


class ColorPrint:
    def __init__(self, stdout=sys.stdout, stderr=sys.stderr):
        self.stdout_pipe = stdout
        self.stderr_pipe = stderr
        self.table = {
            '': '\033[0m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'r': '\033[31m',
            'g': '\033[32m',
            'y': '\033[33m',
            'b': '\033[34m',
            'm': '\033[35m',
            'c': '\033[36m'
        }

    def print(self, format, *args, **kwargs):
        self.__print(self.stdout_pipe, format, *args, **kwargs)

    def error(self, format, *args, **kwargs):
        self.__print(self.stderr_pipe, format, *args, **kwargs)

    def __print(self, pipe, format, end='\n', *args, **kwargs):
        cur = format
        for cmd, color in self.table.items():
            cur = cur.replace('{!' + cmd + '}', color)
        pipe.write(cur.format(*args, **kwargs) + self.table[''] + end)
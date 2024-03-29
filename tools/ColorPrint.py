import sys


class ColorPrint:
    """
    Simple class to allow colored printing using custom string format syntax.
    """

    def __init__(self, stdout=sys.stdout, stderr=sys.stderr, name=None):
        """
        Setup a ColorPrint object with given stdout and stderr pipes
        """

        self.name = name
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

    def print(self, format_string, *args, **kwargs):
        """
        Print to stdout using string .format()
        Additional syntax: {!<color>} is replaced by the necessary codes.
        Available colors: 'red','green','yellow','blue','magenta','cyan',''
        {!} results in colors to be reset.
        """

        self.__print(self.stdout_pipe, format_string, *args, **kwargs)

    def error(self, format_string, *args, **kwargs):
        """
        Print to stderr using string .format()
        Additional syntax: {!<color>} is replaced by the necessary codes.
        Available colors: 'red','green','yellow','blue','magenta','cyan',''
        {!} results in colors to be reset.
        """
        self.__print(self.stderr_pipe, format_string, *args, **kwargs)

    def __print(self, pipe, format_string, end='\n'):
        if self.name is not None:
            cur = '[' + self.name + '] ' + format_string
        else:
            cur = format_string
        for cmd, color in self.table.items():
            cur = cur.replace('{!' + cmd + '}', color)
        pipe.write(cur + self.table[''] + end)

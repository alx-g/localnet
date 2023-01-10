import subprocess

from tools import ColorPrint


class mysubprocess:
    def __init__(self, name):
        self.c = ColorPrint(name=name)

    def check_call(self, *args, **kwargs) -> int:
        if len(args) > 0:
            cmd = args[0]
        else:
            cmd = kwargs['args']

        self.c.print("{!y} Run: %s" % (subprocess.list2cmdline(cmd),))
        try:
            ret = subprocess.check_call(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            self.c.error("{!r} Done, $?: %d, error: %s" % (e.returncode, e.stderr))
            raise e
        else:
            self.c.print("{!g} Done, $?: %d" % (0,))
            return ret

    def check_output(self, *args, **kwargs) -> str:
        if len(args) > 0:
            cmd = args[0]
        else:
            cmd = kwargs['args']

        self.c.print("{!y} Run: %s" % (subprocess.list2cmdline(cmd),))
        try:
            out = subprocess.check_output(*args, **kwargs).decode()
        except subprocess.CalledProcessError as e:
            self.c.error(
                "{!r} Done, $?: %d, output: %s, error: %s" % (e.returncode, e.stdout.decode().strip(), e.stderr))
            raise e
        else:
            self.c.print("{!g} Done, $?: %d, output: %s" % (0, out.strip()))
            return out

    def Popen(self, *args, **kwargs):
        if len(args) > 0:
            cmd = args[0]
        else:
            cmd = kwargs['args']

        self.c.print("{!y} Run: %s" % (subprocess.list2cmdline(cmd),))

        return subprocess.Popen(*args, **kwargs)

import subprocess


class mysubprocess:
    def __init__(self, debug: bool, target):
        self.debug = debug
        self.target = target

    def check_call(self, *args, **kwargs) -> int:
        if len(args)>0:
            cmd = args[0]
        else:
            cmd = kwargs['args']

        if self.debug:
            self.target.write("[LOCALNET] Run: %s\n" % (subprocess.list2cmdline(cmd),))
        try:
            ret = subprocess.check_call(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            if self.debug:
                self.target.write("[LOCALNET] Done, $?: %d, error: %s\n" % (e.returncode, e.stderr))
            raise e
        else:
            if self.debug:
                self.target.write("[LOCALNET] Done, $?: %d\n" % (0,))
            return ret

    def check_output(self, *args, **kwargs) -> str:
        if len(args)>0:
            cmd = args[0]
        else:
            cmd = kwargs['args']

        if self.debug:
            self.target.write("[LOCALNET] Run: %s\n" % (subprocess.list2cmdline(cmd),))
        try:
            out = subprocess.check_output(*args, **kwargs).decode()
        except subprocess.CalledProcessError as e:
            if self.debug:
                self.target.write("[LOCALNET] Done, $?: %d, output: %s, error: %s\n" % (e.returncode, e.stdout, e.stderr))
            raise e
        else:
            if self.debug:
                self.target.write("[LOCALNET] Done, $?: %d, output: %s\n" % (0, out))
            return out

    def Popen(self, *args, **kwargs):
        if len(args)>0:
            cmd = args[0]
        else:
            cmd = kwargs['args']

        if self.debug:
            self.target.write("[LOCALNET] Run: %s\n" % (subprocess.list2cmdline(cmd),))

        return subprocess.Popen(*args, **kwargs)

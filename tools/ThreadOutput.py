import queue
import sys
import threading
import time


class ThreadOutput:
    """
    This class enables simplistic capturing and retrieving output from subprocesses while they are running.
    """

    def __init__(self, prefix):
        """
        Create ThreadOutput object, output using the dump method will be prefixed by '[prefix] '.
        """
        self.prefix = prefix
        self.pipe = None
        self.queue = queue.Queue()
        self.thread = None
        self.sub = None
        self.running = True

    def register(self, sub):
        """
        Set subprocess to capture output from.
        """
        self.pipe = sub.stdout
        self.sub = sub

    def runner(self):
        """
        This polling function runs in a separate thread and captures the output of the subprocess.
        """
        while self.running:
            line = self.pipe.readline()
            if not line == b'':
                self.queue.put(line)
            else:
                time.sleep(0.1)

    def dump(self):
        """
        This function can be called to dump the current captured contents to stdout.
        Contents will be prefixed by '[prefix] '
        """

        try:
            while True:
                lines = self.queue.get(False).decode()
                out = ''
                for line in lines.rstrip('\n').split('\n'):
                    out += '[%s] %s\n' % (self.prefix, line)
                sys.stdout.write(out)
        except queue.Empty:
            pass

    def stop(self):
        """
        Stop polling subprocess output and join running thread.
        """
        self.running = False
        self.thread.join()

    def start(self):
        """
        Start polling subprocess output.
        """
        self.thread = threading.Thread(target=self.runner)
        self.thread.daemon = True
        self.thread.start()

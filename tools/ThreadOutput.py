import time
import sys
import queue
import threading


class ThreadOutput:
    def __init__(self, prefix):
        self.prefix = prefix
        self.pipe = None
        self.queue = queue.Queue()
        self.thread = None
        self.sub = None
        self.running = True

    def register(self, sub):
        self.pipe = sub.stdout
        self.sub = sub

    def runner(self):
        while self.running:
            l = self.pipe.readline()
            if not l == b'':
                self.queue.put(l)
            else:
                time.sleep(0.1)

    def dump(self):
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
        self.running = False
        self.thread.join()

    def start(self):
        self.thread = threading.Thread(target=self.runner)
        self.thread.daemon = True
        self.thread.start()

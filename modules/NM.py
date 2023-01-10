import argparse
import subprocess

import tools
from modules import BaseModule


class NM(BaseModule):
    """
    Module to configure NetworkManager to set 'managed' flag of interface.
    """

    def __init__(self):
        self.running = False
        self.c = tools.ColorPrint(name=self.__class__.__name__)
        self.subprocess = tools.mysubprocess(self.__class__.__name__)

        self.local_interface = None
        self.binary = tools.locate('nmcli')
        if self.binary is None:
            self.c.error('{!r}Could not find nmcli.')
            self.disabled = True
        else:
            try:
                self.version = self.subprocess.check_output([self.binary, '--version'],
                                                            stderr=subprocess.STDOUT).strip()
                if not self.version:
                    self.c.error('{!r}The NM module could not detect nmcli version.')
                    self.disabled = True
            except:
                self.c.error('{!r}The NM module could not run nmcli.')
                self.disabled = True
            else:
                self.disabled = False
        if self.disabled:
            self.c.print('{!y}Assuming option --no-nm.')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        parser.add_argument('--no-nm', action='store_true', default=False, help='Do not configure NetworkManager.')

    def configure(self, args):
        if not self.disabled:
            self.disabled = args.no_nm
        self.local_interface = args.local_interface

    def start(self):
        if not self.disabled:
            self.subprocess.check_call(['nmcli', 'dev', 'set', self.local_interface, 'managed', 'no'])
        self.running = True

    def status(self):
        pass

    def stop(self):
        if not self.disabled and self.running:
            self.subprocess.check_call(['nmcli', 'dev', 'set', self.local_interface, 'managed', 'yes'])
        self.running = False

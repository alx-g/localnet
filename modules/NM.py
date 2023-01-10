import argparse
import subprocess
import sys

import tools
from modules import BaseModule


class NM(BaseModule):
    """
    Module to configure NetworkManager to set 'managed' flag of interface.
    """

    def __init__(self):
        self.subprocess = tools.mysubprocess(True, sys.stdout)
        self.local_interface = None
        self.binary = tools.locate('nmcli')
        if self.binary is None:
            print('Could not find nmcli.')
            self.disabled = True
        else:
            try:
                self.version = self.subprocess.check_output([self.binary, '--version'],
                                                       stderr=subprocess.STDOUT).strip()
                if not self.version:
                    print('The NM module could not detect nmcli version.')
                    self.disabled = True
            except:
                print('The NM module could not run nmcli.')
                self.disabled = True
            else:
                self.disabled = False
        if self.disabled:
            print('Assuming option --no-nm.')

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

    def status(self):
        pass

    def stop(self):
        if not self.disabled:
            self.subprocess.check_call(['nmcli', 'dev', 'set', self.local_interface, 'managed', 'yes'])

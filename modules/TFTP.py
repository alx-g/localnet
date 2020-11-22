import argparse
import os
import subprocess

import tools
from modules import BaseModule


class TFTP(BaseModule):
    def __init__(self):
        # This module requires unbound
        self.binary = tools.locate('in.tftpd')
        if self.binary is None:
            raise FileNotFoundError('The TFTP module requires tftpd to be installed and on $PATH.')

        try:
            self.version = subprocess.check_output(['tftpd', '--version'],
                                                   stderr=subprocess.STDOUT).decode().strip()
            if not self.version:
                raise RuntimeError('The TFTP module could not detect tftpd version.')
        except:
            raise RuntimeError('The TFTP module could not run tftpd.')

        self.stdout = tools.ThreadOutput('TFTP')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        parser.add_argument('--tftp-pidfile', action='store', type=str, default='/run/tftpd.pid',
                            help='Set path for tftpd pidfile, default is "/run/tftpd.pid"')
        parser.add_argument('--tftp-rootdir', action='store', type=str, default='/srv/tftp/',
                            help='Set path for tftpd root directory, default is "/srv/tftp/"')

    def configure(self, args):
        self.rootdir = args.tftp_rootdir
        self.pidfile = args.tftp_pidfile

    def start(self):
        self.process = subprocess.Popen(
            [self.binary, '-L', '--secure', self.rootdir, '--pidfile', self.pidfile],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.stdout.register(self.process)
        self.stdout.start()

    def status(self):
        pass

    def stop(self):
        self.process.terminate()
        self.stdout.stop()

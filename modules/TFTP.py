import argparse
import subprocess
import sys

import tools
from modules import BaseModule


class TFTP(BaseModule):
    """
    Module to configure and start tftpd independently from system config.
    """

    def __init__(self):
        self.rootdir = None
        self.pidfile = None
        self.process = None
        self.enabled = True
        self.enabled_user = None

        # This module requires tftpd
        self.binary = tools.locate('in.tftpd')
        if self.binary is None:
            print('The TFTP module requires tftpd (specifically in.tftpd) to be installed and on $PATH.',
                  file=sys.stderr)
            self.enabled = False
        else:
            try:
                self.version = subprocess.check_output(['tftpd', '--version'],
                                                       stderr=subprocess.STDOUT).decode().strip()
                if not self.version:
                    print('The TFTP module could not detect tftpd version.', file=sys.stderr)
                    self.enabled = False
            except:
                print('The TFTP module could not run tftpd.', file=sys.stderr)
                self.enabled = False

        self.stdout = tools.ThreadOutput('TFTP')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        parser.add_argument('--tftp-pidfile', action='store', type=str, default='/run/tftpd.pid',
                            help='Set path for tftpd pidfile, default is "/run/tftpd.pid"')
        parser.add_argument('--tftp-rootdir', action='store', type=str, default='/srv/tftp/',
                            help='Set path for tftpd root directory, default is "/srv/tftp/"')

    def configure(self, args):
        if not self.enabled and args.pxe:
            print('TFTP module requested for network booting, but it will not run!', file=sys.stderr)

        self.rootdir = args.tftp_rootdir
        self.pidfile = args.tftp_pidfile
        self.enabled_user = self.enabled and args.pxe

    def start(self):
        if not self.enabled_user:
            return

        self.process = subprocess.Popen(
            [self.binary, '-L', '--secure', self.rootdir, '--pidfile', self.pidfile],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.stdout.register(self.process)
        self.stdout.start()

    def status(self):
        pass

    def stop(self):
        if not self.enabled_user:
            return
        self.process.terminate()
        self.stdout.stop()

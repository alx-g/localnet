import argparse
import os
import subprocess
import sys
import tempfile
import textwrap
import re

import tools
from modules import BaseModule


class DNS(BaseModule):
    """
    Module to configure and start unbound independently from system config.
    """

    def __init__(self):
        self.mask = None
        self.ip = None
        self.configfile = None
        self.process = None
        self.enabled = True
        self.enabled_user = None

        # This module requires unbound
        self.binary = tools.locate('unbound')
        if self.binary is None:
            print('The DNS module requires unbound to be installed and on $PATH.', file=sys.stderr)
            self.enabled = False
        else:
            try:
                p = subprocess.Popen([self.binary, '-V'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                [out,err] = p.communicate()
                version_response = out.decode().strip()
                find_version = re.compile(r'Version\s*(?P<version>[\d\.]+)')
                match = find_version.search(version_response)
                if not match:
                    print('The DNS module could not detect unbound version.', file=sys.stderr)
                    self.enabled = False
                else:
                    
                    self.version = match.groupdict()['version']
                    if not self.version:
                        print('The DNS module could not detect unbound version.', file=sys.stderr)
                        self.enabled = False
            except:
                print('The DNS module could not run ubound.', file=sys.stderr)
                self.enabled = False

        self.stdout = tools.ThreadOutput('DNS')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        pass

    def configure(self, args):
        if not self.enabled and (args.internet_interface is not None):
            print('DNS module requested, but it will not run!', file=sys.stderr)

        self.enabled_user = self.enabled and (args.internet_interface is not None)
        self.mask = args.subnet
        self.ip = args.ip

    def start(self):
        if not self.enabled_user:
            return

        self.configfile = tempfile.mkstemp(suffix='.conf', prefix='localnet_')[1]

        subnet_bytes = self.mask // 8
        subnet0 = '.'.join(self.ip.split('.')[:subnet_bytes]) + '.0' * (4 - subnet_bytes)

        config = textwrap.dedent('''
                    server:
                        verbosity: 1
                        interface: {ip}
                        access-control: {subnet0}/{mask_bits} allow
                ''').format(
            ip=self.ip,
            subnet0=subnet0,
            mask_bits=self.mask
        )
        with open(self.configfile, 'w') as f:
            f.write(config)

        # Start DNS server
        self.process = subprocess.Popen(
            [self.binary, '-d', '-c', self.configfile],
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
        os.remove(self.configfile)

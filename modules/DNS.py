import argparse
import os
import re
import subprocess
import tempfile
import textwrap

import tools
from modules import BaseModule


class DNS(BaseModule):
    """
    Module to configure and start unbound independently from system config.
    """

    def __init__(self):
        self.c = tools.ColorPrint(name=self.__class__.__name__)
        self.subprocess = tools.mysubprocess(self.__class__.__name__)
        self.mask = None
        self.ip = None
        self.configfile = None
        self.process = None
        self.enabled = True
        self.enabled_user = None

        # This module requires unbound
        self.binary = tools.locate('unbound')
        if self.binary is None:
            self.c.error('{!r}The DNS module requires unbound to be installed and on $PATH.')
            self.enabled = False
        else:
            try:
                version_response = self.subprocess.check_output([self.binary, '-V'], stderr=subprocess.STDOUT).strip()
                find_version = re.compile(r'Version\s*(?P<version>[\d\.]+)')
                match = find_version.search(version_response)
                if not match:
                    self.c.error('{!r}The DNS module could not detect unbound version.')
                    self.enabled = False
                else:

                    self.version = match.groupdict()['version']
                    if not self.version:
                        self.c.error('{!r}The DNS module could not detect unbound version.')
                        self.enabled = False
            except:
                self.c.error('{!r}The DNS module could not run ubound.')
                self.enabled = False

        self.stdout = tools.ThreadOutput('DNS')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        pass

    def configure(self, args):
        if not self.enabled and (args.internet_interface is not None):
            self.c.error('{!r}DNS module requested, but it will not run!')

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
        self.process = self.subprocess.Popen(
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

import argparse
import os
import subprocess
import tempfile
import textwrap

import tools
from modules import BaseModule


class DNS(BaseModule):
    def __init__(self):
        # This module requires unbound
        self.binary = tools.locate('unbound')
        if self.binary is None:
            raise FileNotFoundError('The DNS module requires unbound to be installed and on $PATH.')

        try:
            vstring = subprocess.check_output([self.binary, '-V'],
                                              stderr=subprocess.STDOUT).decode().strip()
            self.version = vstring.split('\n')[0].replace('Version', '').strip()
            if not self.version:
                raise RuntimeError('The DNS module could not detect unbound version.')
        except:
            raise RuntimeError('The DNS module could not run ubound.')

        self.stdout = tools.ThreadOutput('DNS')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        pass

    def configure(self, args):
        self.mask = args.subnet
        self.ip = args.ip

    def start(self):
        self.configfile = tempfile.mkstemp(suffix='.conf', prefix='localnet_')[1]

        subnet_bytes = self.mask // 8
        subnet0 = '.'.join(self.ip.split('.')[:subnet_bytes]) + '.0' * (4 - subnet_bytes)

        config = textwrap.dedent('''
                    server:
                        verbosity: 1
                        interface: {ip}
                        access-control: {subnet0}/{maskbits} allow
                ''').format(
            ip=self.ip,
            subnet0=subnet0,
            maskbits=self.mask
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
        self.process.terminate()
        self.stdout.stop()
        os.remove(self.configfile)

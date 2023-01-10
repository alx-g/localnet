import argparse
import subprocess

import tools
from modules import BaseModule


class NAT(BaseModule):
    """
    Module to reconfigure nftables independently from system config.
    """

    def __init__(self):
        self.c = tools.ColorPrint(name=self.__class__.__name__)
        self.subprocess = tools.mysubprocess(self.__class__.__name__)

        self.local_interface = None
        self.internet_interface = None
        self.enabled = True
        self.enabled_user = True
        self.sysctl_backup = None
        self.subnet_definiton = None

        # This module requires nft
        self.binary = tools.locate('nft')
        if self.binary is None:
            self.c.error('{!r}The NAT module requires nft (nftables) to be installed and on $PATH.')
            self.enabled = False
        else:
            try:
                self.version = self.subprocess.check_output([self.binary, '-v'],
                                                            stderr=subprocess.STDOUT).strip()

                if not self.version:
                    self.c.error('{!r}The NAT module could not detect nft (nftables) version.')
                    self.enabled = False
            except:
                self.c.error('{!r}The NAT module could not run nft (nftables).')
                self.enabled = False

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        pass

    def configure(self, args):
        if not self.enabled and (args.internet_interface is not None):
            self.c.error('{!r}NAT module requested to bridge interfaces, but it will not run!')

        self.local_interface = args.local_interface
        self.internet_interface = args.internet_interface
        self.enabled_user = (self.internet_interface is not None) and self.enabled
        ip_addr = str(args.ip).split('.')
        mask_bytes = int(args.subnet) // 8
        ip_addr2 = ip_addr[:mask_bytes] + (4 - mask_bytes) * ['0']
        self.subnet_definiton = '.'.join(ip_addr2) + '/' + str(int(args.subnet))

    def start(self):
        if not self.enabled_user:
            return

        # Store old val
        self.sysctl_backup = self.subprocess.check_output(['sysctl', 'net.ipv4.ip_forward'],
                                                          stderr=subprocess.STDOUT).strip()

        # Enable forwarding
        self.subprocess.check_call(['sysctl', 'net.ipv4.ip_forward=1'])

        # Add a custom temporary nft table
        self.subprocess.check_call(['nft', 'add table ip localnet'])
        self.subprocess.check_call(['nft', 'add chain ip localnet forward { type filter hook forward priority -10 ; }'])
        self.subprocess.check_call(['nft', 'add rule localnet forward ct state vmap '
                                           '{ established : accept, related : accept, invalid : drop }'])
        self.subprocess.check_call(['nft', 'add rule localnet forward iifname %s accept' % (self.local_interface,)])
        self.subprocess.check_call(
            ['nft', 'add chain ip localnet prerouting { type nat hook prerouting priority 90 ; }'])
        self.subprocess.check_call(
            ['nft', 'add chain ip localnet postrouting { type nat hook postrouting priority 90 ; }'])
        self.subprocess.check_call(['nft', 'add rule localnet postrouting ip saddr %s oifname %s masquerade' % (
            self.subnet_definiton, self.internet_interface)])

    def status(self):
        pass

    def stop(self):
        if not self.enabled_user:
            return

        # Restore forwarding val
        self.subprocess.check_call(['sysctl', self.sysctl_backup.replace(' ', '')])

        try:
            self.subprocess.check_call(['nft', 'flush', 'chain', 'localnet', 'postrouting'])
        except:
            pass
        try:
            self.subprocess.check_call(['nft', 'flush', 'chain', 'localnet', 'forward'])
        except:
            pass
        try:
            self.subprocess.check_call(['nft', 'delete', 'chain', 'ip', 'localnet', 'prerouting'])
        except:
            pass
        try:
            self.subprocess.check_call(['nft', 'delete', 'chain', 'ip', 'localnet', 'postrouting'])
        except:
            pass
        try:
            self.subprocess.check_call(['nft', 'delete', 'chain', 'ip', 'localnet', 'forward'])
        except:
            pass

        self.subprocess.check_call(['nft', 'delete', 'table', 'ip', 'localnet'])

import argparse
import subprocess
import sys

import tools
from modules import BaseModule


class NAT(BaseModule):
    """
    Module to reconfigure nftables independently from system config.
    """

    def __init__(self):
        self.local_interface = None
        self.internet_interface = None
        self.enabled = True
        self.enabled_user = True
        self.sysctl_backup = None
        self.subnet_definiton = None

        # This module requires nft
        self.binary = tools.locate('nft')
        if self.binary is None:
            print('The NAT module requires nft (nftables) to be installed and on $PATH.', file=sys.stderr)
            self.enabled = False
        else:
            try:
                self.version = subprocess.check_output([self.binary, '-v'],
                                                       stderr=subprocess.STDOUT).decode().strip()

                if not self.version:
                    print('The NAT module could not detect nft (nftables) version.', file=sys.stderr)
                    self.enabled = False
            except:
                print('The NAT module could not run nft (nftables).', file=sys.stderr)
                self.enabled = False

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        pass

    def configure(self, args):
        if not self.enabled and (args.internet_interface is not None):
            print('NAT module requested to bridge interfaces, but it will not run!', file=sys.stderr)

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
        self.sysctl_backup = subprocess.check_output(['sysctl', 'net.ipv4.ip_forward'], stderr=subprocess.STDOUT)

        # Enable forwarding
        subprocess.check_call(['sysctl', 'net.ipv4.ip_forward=1'])

        # Add a custom temporary nft table
        subprocess.check_call(['nft', 'add table ip localnet'])
        subprocess.check_call(['nft', 'add chain ip localnet forward { type filter hook forward priority -10 ; }'])
        subprocess.check_call(['nft', 'add rule localnet forward ct state vmap '
                                      '{ established : accept, related : accept, invalid : drop }'])
        subprocess.check_call(['nft', 'add rule localnet forward iifname %s accept' % (self.local_interface,)])
        subprocess.check_call(['nft', 'add chain ip localnet prerouting { type nat hook prerouting priority 90 ; }'])
        subprocess.check_call(['nft', 'add chain ip localnet postrouting { type nat hook postrouting priority 90 ; }'])
        subprocess.check_call(['nft', 'add rule localnet postrouting ip saddr %s oifname %s masquerade' % (
            self.subnet_definiton, self.internet_interface)])

    def status(self):
        pass

    def stop(self):
        if not self.enabled_user:
            return

        # Restore forwarding val
        subprocess.check_call(['sysctl', self.sysctl_backup.decode().replace(' ', '')])

        try:
            subprocess.check_call(['nft', 'flush', 'chain', 'localnet', 'postrouting'])
        except:
            pass
        try:
            subprocess.check_call(['nft', 'flush', 'chain', 'localnet', 'forward'])
        except:
            pass
        try:
            subprocess.check_call(['nft', 'delete', 'chain', 'ip', 'localnet', 'prerouting'])
        except:
            pass
        try:
            subprocess.check_call(['nft', 'delete', 'chain', 'ip', 'localnet', 'postrouting'])
        except:
            pass
        try:
            subprocess.check_call(['nft', 'delete', 'chain', 'ip', 'localnet', 'forward'])
        except:
            pass

        subprocess.check_call(['nft', 'delete', 'table', 'ip', 'localnet'])

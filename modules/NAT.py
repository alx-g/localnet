import argparse
import subprocess
import textwrap

import tools
from modules import BaseModule


class NAT(BaseModule):
    """
    Module to reconfigure iptables independently from system config.
    """

    def __init__(self):
        self.local_interface = None
        self.internet_interface = None
        self.enabled = None
        self.sysctl_backup = None
        self.iptables_backup = None

        # This module requires iptables
        self.binary = tools.locate('iptables')
        if self.binary is None:
            raise FileNotFoundError('The NAT module requires iptables to be installed and on $PATH.')

        try:
            self.version = subprocess.check_output([self.binary, '-V'],
                                                   stderr=subprocess.STDOUT).decode().strip()

            if not self.version:
                raise RuntimeError('The NAT module could not detect iptables version.')
        except:
            raise RuntimeError('The NAT module could not run iptables.')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        pass

    def configure(self, args):
        self.local_interface = args.local_interface
        self.internet_interface = args.internet_interface
        self.enabled = self.internet_interface is not None

    def start(self):
        if not self.enabled:
            return

        # backup config
        self.iptables_backup = subprocess.check_output(['iptables-save'])

        # load custom config
        cfg = textwrap.dedent('''
        *security
        :INPUT ACCEPT [0:0]
        :FORWARD ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        COMMIT
        *raw
        :PREROUTING ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        COMMIT
        *mangle
        :PREROUTING ACCEPT [0:0]
        :INPUT ACCEPT [0:0]
        :FORWARD ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        :POSTROUTING ACCEPT [0:0]
        COMMIT
        *filter
        :INPUT ACCEPT [0:0]
        :FORWARD ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
        -A FORWARD -i {interface_local} -o {interface_internet} -j ACCEPT
        COMMIT
        *nat
        :PREROUTING ACCEPT [0:0]
        :INPUT ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        :POSTROUTING ACCEPT [0:0]
        -A POSTROUTING -o {interface_internet} -j MASQUERADE
        COMMIT
        ''').format(
            interface_local=self.local_interface,
            interface_internet=self.internet_interface
        )

        # Store old val
        self.sysctl_backup = subprocess.check_output(['sysctl', 'net.ipv4.ip_forward'], stderr=subprocess.STDOUT)

        # Enable forwarding
        subprocess.check_call(['sysctl', 'net.ipv4.ip_forward=1'])

        proc = subprocess.Popen(['iptables-restore'], stdin=subprocess.PIPE)
        proc.communicate(input=cfg.encode())
        proc.wait()
        if not proc.returncode == 0:
            proc2 = subprocess.Popen(['iptables-restore'], stdin=subprocess.PIPE)
            proc2.communicate(input=self.iptables_backup)
            proc2.wait()
            raise RuntimeError('Could not configure iptables, tried to restore prev config...')

    def status(self):
        pass

    def stop(self):
        if not self.enabled:
            return

        # Restore forwarding val
        subprocess.check_call(['sysctl', self.sysctl_backup.decode().replace(' ', '')])

        proc = subprocess.Popen(['iptables-restore'], stdin=subprocess.PIPE)
        proc.communicate(input=self.iptables_backup)
        proc.wait()
        if not proc.returncode == 0:
            raise RuntimeError('Could not restore iptables config...')

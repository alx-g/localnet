import argparse
import os
import subprocess
import sys
import tempfile
import textwrap

import tools
from modules import BaseModule


class DHCP(BaseModule):
    """
    Module to configure and start dhcpd independently from system config.
    """

    def __init__(self):
        self.ip = None
        self.mask = None
        self.range = None
        self.domain = None
        self.pxe_file = None
        self.local_interface = None
        self.pidfile = None
        self.configfile = None
        self.process = None

        # This module requires dhcpd
        self.binary = tools.locate('dhcpd')
        if self.binary is None:
            print('The DHCP module requires dhcpd to be installed and on $PATH. This is mandatory.', file=sys.stderr)
            sys.exit(1)

        try:
            self.version = subprocess.check_output([self.binary, '--version'],
                                                   stderr=subprocess.STDOUT).decode().strip()
            if not self.version:
                print('The DHCP module could not detect dhcpd version. This is mandatory.', file=sys.stderr)
                sys.exit(1)
        except:
            print('The DHCP module could not run dhcpd. This is mandatory.', file=sys.stderr)
            sys.exit(1)

        self.stdout = tools.ThreadOutput('DHCP')

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        parser.add_argument('--dhcp-pidfile', action='store', type=str, default='/run/dhcpd.pid',
                            help='Set path for dhcpd pidfile, default is "/run/dhcpd.pid"')

    def configure(self, args):
        self.ip = args.ip
        self.mask = args.subnet
        self.range = args.iprange
        self.domain = args.domain
        self.pxe_file = args.pxe
        self.local_interface = args.local_interface
        self.pidfile = args.dhcp_pidfile

    def start(self):
        self.configfile = tempfile.mkstemp(suffix='.conf', prefix='localnet_')[1]

        subnet_bytes = self.mask // 8
        subnet0 = '.'.join(self.ip.split('.')[:subnet_bytes]) + '.0' * (4 - subnet_bytes)
        broadcast = '.'.join(self.ip.split('.')[:subnet_bytes]) + '.255' * (4 - subnet_bytes)
        mask = '255' + '.255' * (subnet_bytes - 1) + '.0' * (4 - subnet_bytes)

        config = textwrap.dedent('''
            option domain-name "{domain}";
            default-lease-time 600;
            max-lease-time 7200;
            log-facility local7;
            {boot_comment}allow booting;
            subnet {subnet0} netmask {subnet_mask} {{
                range {range};
                option broadcast-address {broadcast};
                option routers {ip};
                option domain-name-servers {ip};
                default-lease-time 14400;
                max-lease-time 28800;
                {boot_comment}filename "{pxe_file}";
                {boot_comment}next-server {ip};
            }}
        ''').format(
            domain=self.domain,
            boot_comment=('' if self.pxe_file else '# '),
            subnet0=subnet0,
            subnet_mask=mask,
            range=self.range,
            broadcast=broadcast,
            ip=self.ip,
            pxe_file=self.pxe_file
        )
        with open(self.configfile, 'w') as f:
            f.write(config)

        # Setup interface and static ip
        subprocess.check_call(['ip', 'link', 'set', 'up', 'dev', self.local_interface])
        subprocess.check_call(['ip', 'address', 'flush', 'dev', self.local_interface])
        subprocess.check_call(['ip', 'address', 'add', '%s/%d' % (self.ip, self.mask), 'dev', self.local_interface])

        # Start DHCPD
        self.process = subprocess.Popen(
            [self.binary, '-4', '-f', '-cf', self.configfile, '-pf', self.pidfile, self.local_interface],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.stdout.register(self.process)
        self.stdout.start()

    def status(self):
        pass

    def stop(self):
        self.process.terminate()
        self.stdout.stop()
        subprocess.check_call(['ip', 'address', 'flush', 'dev', self.local_interface])
        os.remove(self.configfile)

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
        self.enabled = True

        # This module requires dhcpd
        self.dhcpd_binary = tools.locate('dhcpd')
        if self.dhcpd_binary is None:
            print('The DHCP module requires dhcpd to be installed and on $PATH. This is mandatory.', file=sys.stderr)
            self.enabled = False
        else:
            try:
                self.dhcpd_version = subprocess.check_output([self.dhcpd_binary, '--version'],
                                                             stderr=subprocess.STDOUT).decode().strip()
                if not self.dhcpd_version:
                    print('The DHCP module could not detect dhcpd version. This is mandatory.', file=sys.stderr)
                    self.enabled = False
            except:
                print('The DHCP module could not run dhcpd. This is mandatory.', file=sys.stderr)
                self.enabled = False

        self.ip_binary = tools.locate('ip')
        if self.ip_binary is None:
            print('The DHCP module requires "ip" to be installed and on $PATH. This is mandatory.', file=sys.stderr)
            self.enabled = False

        try:
            self.ip_version = subprocess.check_output([self.ip_binary, '-V'], stderr=subprocess.STDOUT).decode().strip()

            if not self.ip_version:
                print('The DHCP module could not detect "ip" version. This is mandatory.', file=sys.stderr)
                self.enabled = False
        except:
            print('The DHCP module could not run "ip". This is mandatory.', file=sys.stderr)
            self.enabled = False

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
        if not self.enabled:
            print('Cannot run DHCP module. exiting.', file=sys.stderr)
            sys.exit(1)

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
        try:
            subprocess.check_call([self.ip_binary, 'link', 'set', 'up', 'dev', self.local_interface])
            subprocess.check_call([self.ip_binary, 'address', 'flush', 'dev', self.local_interface])
            subprocess.check_call([self.ip_binary, 'address', 'add', '%s/%d' % (self.ip, self.mask), 'dev',
                                   self.local_interface])
        except subprocess.CalledProcessError as e:
            if e.returncode == 2:
                print('The "ip" command indicated that the kernel reported an error. Did you run this script with'
                      'elevated privileges?')
                sys.exit(100)

        # Start DHCPD
        self.process = subprocess.Popen(
            [self.dhcpd_binary, '-4', '-f', '-cf', self.configfile, '-pf', self.pidfile, self.local_interface],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.stdout.register(self.process)
        self.stdout.start()

    def status(self):
        pass

    def stop(self):
        if not self.enabled:
            return

        self.process.terminate()
        self.stdout.stop()
        subprocess.check_call([self.ip_binary, 'address', 'flush', 'dev', self.local_interface])
        os.remove(self.configfile)

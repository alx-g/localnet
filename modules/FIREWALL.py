import argparse
import sys
import subprocess
from typing import List

import tools
from modules import BaseModule


class FIREWALL(BaseModule):
    """
    Module to reconfigure firewalld/ufw to allow packet forwarding.
    """
    SUPPORTED = {'firewall-cmd': 'firewall daemon'}

    def __init__(self):
        self.subprocess = tools.mysubprocess(True, sys.stdout)

        self.local_interface = None
        self.internet_interface = None
        self.firewall_type = None
        self.enabled = True
        self.local_zone = None
        self.internet_zone = None
        self.query_forward = None
        self.dns_allowed = None

        firewalls_detected = FIREWALL.find_available()
        if len(firewalls_detected) == 0:
            print('The FIREWALL module found no installed firewall cmd tools, this may still be ok. '
                  'This module will not run!')
            self.enabled = False
        elif len(firewalls_detected) == 1:
            self.firewall_type = firewalls_detected[0]
        else:
            print('The FIREWALL module found multiple installed firewall cmd tools, please specify by argument which '
                  'one to use. This module will not run!', file=sys.stderr)
            self.enabled = False

        self.binary = tools.locate(self.firewall_type)
        if self.binary is None:
            print('The FIREWALL module could not find the cmd tool for the configured firewall type. This module will '
                  'not run!', file=sys.stderr)
            self.enabled = False

    @staticmethod
    def register_args(parser: argparse.ArgumentParser):
        parser.add_argument('--firewall-type', action='store', type=str, default=None,
                            help='Set firewall type to configure manually, selected automatically by default')

    @staticmethod
    def find_available() -> List[str]:
        found: List[str] = []
        for item in FIREWALL.SUPPORTED.keys():
            if tools.locate(item) is not None:
                found.append(item)

        return found

    def configure(self, args):
        if args.firewall_type is None:
            self.firewall_type = None
        else:
            if str(args.firewall_type) not in FIREWALL.SUPPORTED.keys():
                print('FIREWALL module does not recognize firewall type "%s". This module will not run!', file=sys.stderr)
                self.enabled = False

        self.local_interface = args.local_interface
        self.internet_interface = args.internet_interface

    def start(self):
        if not self.enabled:
            return
        if self.firewall_type == 'firewall-cmd':
            try:
                self.internet_zone = self.subprocess.check_output(
                    ['firewall-cmd', '--get-zone-of-interface=%s' % (self.internet_interface, )]).strip()
            except subprocess.CalledProcessError:
                print('[FIREWALL] Your main interface is not assigned to a zone, dont know what to do now...', file=sys.stderr)
                self.enabled = False
                return
            try:
                self.local_zone = self.subprocess.check_output(
                    ['firewall-cmd', '--get-zone-of-interface=%s' % (self.local_interface,)]).strip()
            except subprocess.CalledProcessError:
                self.local_zone = None

            if self.local_zone != self.internet_zone:
                if self.local_zone is not None:
                    self.subprocess.check_call(
                        ['firewall-cmd', '--zone=%s' % (self.local_zone,), '--remove-interface=%s' % (self.local_interface,)])
                self.subprocess.check_call(
                    ['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--add-interface=%s' % (self.local_interface,)])

            try:
                self.subprocess.check_call(['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--query-forward'])
                self.query_forward = True
            except subprocess.CalledProcessError:
                self.subprocess.check_call(['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--add-forward'])
                self.query_forward = False

            try:
                self.subprocess.check_call(['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--query-service=dns'])
                self.dns_allowed = True
            except subprocess.CalledProcessError:
                self.subprocess.check_call(['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--add-service=dns'])
                self.dns_allowed = False

    def status(self):
        pass

    def stop(self):
        if not self.enabled:
            return

        if self.firewall_type == 'firewall-cmd':
            if not self.dns_allowed:
                self.subprocess.check_call(['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--remove-service=dns'])

            if not self.query_forward:
                self.subprocess.check_call(['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--remove-forward'])

            if self.local_zone != self.internet_zone:
                self.subprocess.check_call(
                    ['firewall-cmd', '--zone=%s' % (self.internet_zone,), '--remove-interface=%s' % (self.local_interface,)])
                if self.local_zone is not None:
                    self.subprocess.check_call(
                        ['firewall-cmd', '--zone=%s' % (self.local_zone,), '--add-interface=%s' % (self.local_interface,)])




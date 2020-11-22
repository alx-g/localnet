#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

import modules
import tools
from lib import ifaddr


def main(argv):
    dhcp = modules.DHCP()
    nat = modules.NAT()
    dns = modules.DNS()
    tftp = modules.TFTP()

    parser = argparse.ArgumentParser(description="Helper script to create and maintain a local temporary network.")

    parser.add_argument('--interactive', '-i', action='store_true', default=False,
                        help='Enable interactive mode, common parameters not already given will be asked from user interactively.')

    parser.add_argument('local_interface', nargs='?', action='store', type=str, default=None,
                        help='Network interface to use for local network')
    parser.add_argument('internet_interface', nargs='?', action='store', type=str, default=None,
                        help='Network interface with internet access that should be used to bridge the local network to.')

    parser.add_argument('--no-nm', action='store_true', default=False, help='Do not assume NetworkManager is used.')
    parser.add_argument('--ip', action='store', type=str, default='10.10.10.1',
                        help='This computers static ip address, default is 10.10.10.1')
    parser.add_argument('--subnet', action='store', type=int, default=24,
                        help='DHCP subnet mask as number of bits, default is 24. For now only 24,16, and 8 are supported.')
    parser.add_argument('--iprange', action='store', type=str, default='10.10.10.100 10.10.10.200',
                        help='Set address range for DHCP, default is "10.10.10.100 10.10.10.200"')
    parser.add_argument('--domain', action='store', type=str, default='localdomain',
                        help='Set the domain name for the local network, default is "localdomain"')

    parser.add_argument('--pxe', action='store', type=str, default=None,
                        help='Enable PXE network booting with given bootfile. Will start TFTP server. Disabled by default.')

    dhcp.register_args(parser)
    nat.register_args(parser)
    dns.register_args(parser)
    tftp.register_args(parser)

    args = parser.parse_args(argv)

    if not args.interactive:
        if not args.local_interface:
            sys.stderr.write('error: Local interface argument is mandatory when not in interactive mode.\n')
            sys.stderr.flush()
            sys.exit(255)
    else:
        print('Running in interactive mode.')

        if not args.local_interface:
            adapters = ifaddr.get_adapters(include_unconfigured=True)

            options = {}
            suggestion_local = None
            suggestion_internet = None

            for adapter in adapters:
                name = adapter.name
                descr = '' if adapter.nice_name == adapter.name else adapter.nice_name
                if adapter.ips:
                    ips_ = []
                    for ip in adapter.ips:
                        ips_.append("%s/%s" % (ip.ip, ip.network_prefix))
                    descr += 'IP adresses: ' + ', '.join(ips_)
                    suggestion_internet = name
                else:
                    descr += 'No IP adresses assigned to this interface.'
                    suggestion_local = name

                options[name] = descr

            args.local_interface = tools.choose('Available network interfaces', 'Select local_interface', options,
                                                suggestion_local, False)

            args.internet_interface = tools.choose(
                'Do you want to create a bridge to allow internet access in your created network over another '
                'network interface?', 'Select internet_interface or None', options, suggestion_internet, True)

            if not args.pxe:
                args.pxe = tools.ask('Do you want to enable booting over PXE? Enter filename to boot from', args.pxe, str, True)
                if args.pxe:
                    args.tftp_rootdir = tools.ask('Set root directory of TFTP server', args.tftp_rootdir, str, False)

    if not args.no_nm:
        # NetworkManager is used, i.e. interfaces are normally managed. Set the local interface to unmanaged before
        # beginning
        subprocess.check_call(['nmcli', 'dev', 'set', args.local_interface, 'managed', 'no'])

    dhcp.configure(args)
    nat.configure(args)
    dns.configure(args)
    tftp.configure(args)

    dhcp.start()
    nat.start()
    dns.start()
    if args.pxe:
        tftp.start()

    try:
        while True:
            dhcp.stdout.dump()
            dns.stdout.dump()
            if args.pxe:
                tftp.stdout.dump()
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    if args.pxe:
        tftp.stop()
    dhcp.stop()
    nat.stop()
    dns.stop()

    dhcp.stdout.dump()
    dns.stdout.dump()
    tftp.stdout.dump()

    if not args.no_nm:
        # NetworkManager is used, i.e. interfaces are normally managed. Set the local interface to managed again
        subprocess.check_call(['nmcli', 'dev', 'set', args.local_interface, 'managed', 'yes'])


if __name__ == '__main__':
    main(sys.argv[1:])

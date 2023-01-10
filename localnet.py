#!/usr/bin/env python3
import argparse
import sys
import time

import modules
import tools


def main(argv):
    c = tools.ColorPrint(name='LOCALNET')
    c.print('{!b}Registering modules')

    nm = modules.NM()
    dhcp = modules.DHCP()
    nat = modules.NAT()
    dns = modules.DNS()
    firewall = modules.FIREWALL()

    parser = argparse.ArgumentParser(description="Helper script to create and maintain a local temporary network.")

    parser.add_argument('--interactive', '-i', action='store_true', default=False,
                        help='Enable interactive mode, common parameters not already given will be asked from user'
                             'interactively.')

    parser.add_argument('local_interface', nargs='?', action='store', type=str, default=None,
                        help='Network interface to use for local network')
    parser.add_argument('internet_interface', nargs='?', action='store', type=str, default=None,
                        help='Network interface with internet access that should be used to bridge the local network'
                             'to.')

    parser.add_argument('--ip', action='store', type=str, default='10.10.10.1',
                        help='This computers static ip address, default is 10.10.10.1')
    parser.add_argument('--subnet', action='store', type=int, default=24,
                        help='DHCP subnet mask as number of bits, default is 24. For now only 24,16, and 8 are'
                             'supported.')
    parser.add_argument('--iprange', action='store', type=str, default='10.10.10.100 10.10.10.200',
                        help='Set address range for DHCP, default is "10.10.10.100 10.10.10.200"')
    parser.add_argument('--domain', action='store', type=str, default='localdomain',
                        help='Set the domain name for the local network, default is "localdomain"')

    nm.register_args(parser)
    dhcp.register_args(parser)
    nat.register_args(parser)
    dns.register_args(parser)
    firewall.register_args(parser)

    args = parser.parse_args(argv)

    if not args.interactive:
        if not args.local_interface:
            c.error('{!r}Local interface argument is mandatory when not in interactive mode.')
            sys.exit(200)
    else:
        c.print('{!b}Interactive mode')
        args = tools.interactive(args)

    c.print('{!b}Configuring modules')
    nm.configure(args)
    dhcp.configure(args)
    nat.configure(args)
    dns.configure(args)
    firewall.configure(args)

    c.print('{!b}Running modules')
    try:
        nm.start()
        dhcp.start()
        nat.start()
        dns.start()
        firewall.start()

        try:
            while True:
                dhcp.stdout.dump()
                dns.stdout.dump()
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass

    finally:
        c.print('{!b}Stopping modules')
        firewall.stop()
        dns.stop()
        nat.stop()
        dhcp.stop()
        nm.stop()

    dhcp.stdout.dump()
    dns.stdout.dump()

    c.print('{!b}Cleaned up.')


if __name__ == '__main__':
    main(sys.argv[1:])

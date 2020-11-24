from lib import ifaddr
import tools


def interactive(args):
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

    return args
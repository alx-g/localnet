import ifaddr
import tools
from modules.FIREWALL import FIREWALL


def interactive(args):
    firewalls_detected = FIREWALL.find_available()
    if len(firewalls_detected) == 1:
        args.firewall_type = firewalls_detected[0]
    else:
        args.firewall_type = tools.choose('Multiple firewalls found', 'Select the one actively used',
                                          {k: v for k, v in FIREWALL.SUPPORTED.items() if k in firewalls_detected},
                                          '', False)

    adapters = ifaddr.get_adapters(include_unconfigured=True)

    options = {}
    suggestion_local = ''
    suggestion_internet = None

    for adapter in adapters:
        name = adapter.name
        description = '' if adapter.nice_name == adapter.name else adapter.nice_name
        if adapter.ips:
            ips_ = []
            for ip in adapter.ips:
                ips_.append("%s/%s" % (ip.ip, ip.network_prefix))
            description += 'IP addresses: ' + ', '.join(ips_)
            suggestion_internet = name
        else:
            description += 'No IP addresses assigned to this interface.'
            suggestion_local = name

        options[name] = description

    args.local_interface = tools.choose('Available network interfaces', 'Select local_interface', options,
                                        suggestion_local, False)

    args.internet_interface = tools.choose(
        'Do you want to create a bridge to allow internet access in your created network over another '
        'network interface?', 'Select internet_interface or None', options, suggestion_internet, True)

    return args

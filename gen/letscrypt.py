import os
from cmd import add_cmd
import sys

KEYPREFIX = "/etc/letsencrypt/live/"

def get(state):
    for host in state.hosts:
        if 'generate_cert' not in host.props or 'backend_for' not in host.props:
            continue

        yield host

def filter_state(state):
    for host in state.hosts:
        if 'generate_cert' not in host.props:
            continue

        for domain in host.props.get('backend_for', []):
            keydir = os.path.join(KEYPREFIX, domain)

            if not os.path.exists(keydir):
                if 'https' in host.services:
                    host.services.remove('https')

    return state

@add_cmd('generate_cert_domains', False, 0)
def gen(state):
    hostnames = []
    for host in get(state):
        hostnames.extend(host.props['backend_for'])
    return "\n".join(hostnames)

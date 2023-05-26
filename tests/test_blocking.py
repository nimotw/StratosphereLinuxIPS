"""Unit test for modules/blocking/blocking.py
this file needs sudoroot to run
"""
from ..modules.blocking.blocking import Module
from tests.common_test_utils import IS_IN_A_DOCKER_CONTAINER, do_nothing
import platform
import pytest
import os



def has_netadmin_cap():
    """ Check the capabilities given to this docker container"""
    cmd = 'capsh --print | grep "Current:" | cut -d' ' -f3 | grep cap_net_admin'
    output = os.popen(cmd).read()
    return 'cap_net_admin' in output


IS_DEPENDENCY_IMAGE = os.environ.get('IS_DEPENDENCY_IMAGE', False)
# ignore all tests if not using linux
linuxOS = pytest.mark.skipif(
    platform.system() != 'Linux',
    reason='Blocking is supported only in Linux with root priveledges',
)
# When using docker in github actions,  we can't use --cap-add NET_ADMIN
# so all blocking module unit tests will fail because we don't have admin privs
# we use this environment variable to check if slips is
# running in github actions
isroot = pytest.mark.skipif(
    os.geteuid() != 0 or IS_DEPENDENCY_IMAGE is not False,
    reason='Blocking is supported only with root priveledges',
)

# blocking requires net admin capabilities in docker, otherwise skips blocking tests
has_net_admin_cap = pytest.mark.skipif(
    IS_IN_A_DOCKER_CONTAINER and not has_netadmin_cap() ,
    reason='Blocking is supported only with --cap-add=NET_ADMIN',
)


def create_blocking_instance(output_queue, database):
    """Create an instance of blocking.py
    needed by every other test in this file"""
    blocking = Module(output_queue, database)
    # override the print function to avoid broken pipes
    blocking.print = do_nothing
    return blocking

@linuxOS
@isroot
@has_net_admin_cap
def is_slipschain_initialized(output_queue, database) -> bool:
    blocking = create_blocking_instance(output_queue, database)
    output = blocking.get_cmd_output(f'{blocking.sudo} iptables -S')
    rules = [
        '-A INPUT -j slipsBlocking',
        '-A FORWARD -j slipsBlocking',
        '-A OUTPUT -j slipsBlocking',
    ]
    return all(rule in output for rule in rules)

@linuxOS
@isroot
@has_net_admin_cap
def test_initialize_chains_in_firewall(output_queue, database):
    blocking = create_blocking_instance(output_queue, database)
    # manually set the firewall
    blocking.firewall = 'iptables'
    blocking.initialize_chains_in_firewall()
    assert is_slipschain_initialized(output_queue) is True


# todo
# def test_delete_slipsBlocking_chain(output_queue, database):
#     blocking = create_blocking_instance(output_queue, database)
#     # first make sure they are initialized
#     if not is_slipschain_initialized(output_queue):
#         blocking.initialize_chains_in_firewall()
#     os.system('./slips.py -cb')
#     assert is_slipschain_initialized(output_queue) == False

@linuxOS
@isroot
@has_net_admin_cap
def test_block_ip(output_queue, database):
    blocking = create_blocking_instance(output_queue, database)
    blocking.initialize_chains_in_firewall()
    if not blocking.is_ip_blocked('2.2.0.0'):
        ip = '2.2.0.0'
        from_ = True
        to = True
        assert blocking.block_ip(ip, from_, to) is True

@linuxOS
@isroot
@has_net_admin_cap
def test_unblock_ip(output_queue, database):
    blocking = create_blocking_instance(output_queue, database)
    ip = '2.2.0.0'
    from_ = True
    to = True
    # first make sure that it's blocked
    if not blocking.is_ip_blocked('2.2.0.0'):
        assert blocking.block_ip(ip, from_, to) is True
    assert blocking.unblock_ip(ip, from_, to) is True

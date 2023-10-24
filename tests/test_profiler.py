"""Unit test for slips_files/core/performance_profiler.py"""
from tests.module_factory import ModuleFactory
from tests.common_test_utils import do_nothing
import subprocess
import pytest
import json
from slips_files.core.profiler import SUPPORTED_INPUT_TYPES, SEPARATORS



@pytest.mark.parametrize(
    'file,input_type,expected_value',
    [('dataset/test6-malicious.suricata.json', 'suricata', 'suricata')]
)
def test_define_separator_suricata(file, input_type, expected_value, mock_rdb):
    profilerProcess = ModuleFactory().create_profiler_obj()
    with open(file) as f:
        while True:
            sample_flow = f.readline().replace('\n', '')
            # get the first line that isn't a comment
            if not sample_flow.startswith('#'):
                break

    sample_flow = {
        'data': sample_flow,
    }
    profiler_detected_type: str = profilerProcess.define_separator(sample_flow, input_type)
    assert profiler_detected_type == expected_value


@pytest.mark.parametrize(
    'file,input_type,expected_value',
    [('dataset/test10-mixed-zeek-dir/conn.log', 'zeek_log_file', 'zeek-tabs')],
)
def test_define_separator_zeek_tab(file, input_type, expected_value, mock_rdb):
    profilerProcess = ModuleFactory().create_profiler_obj()
    with open(file) as f:
        while True:
            sample_flow = f.readline().replace('\n', '')
            # get the first line that isn't a comment
            if not sample_flow.startswith('#'):
                break

    sample_flow = {
        'data': sample_flow,
    }
    profiler_detected_type: str = profilerProcess.define_separator(sample_flow, input_type)
    assert profiler_detected_type == expected_value


@pytest.mark.parametrize(
    'file, input_type,expected_value',
    [('dataset/test9-mixed-zeek-dir/conn.log', 'zeek_log_file', 'zeek')]
)
def test_define_separator_zeek_dict(file, input_type, expected_value, mock_rdb):
    """
    :param input_type: as determined by slips.py
    """

    profilerProcess = ModuleFactory().create_profiler_obj()
    with open(file) as f:
        sample_flow = f.readline().replace('\n', '')

    sample_flow = json.loads(sample_flow)
    sample_flow = {
        'data': sample_flow,
    }
    profiler_detected_type: str = profilerProcess.define_separator(sample_flow, input_type)
    assert profiler_detected_type == expected_value


@pytest.mark.parametrize('nfdump_file', [('dataset/test1-normal.nfdump')])
def test_define_separator_nfdump(nfdump_file, mock_rdb):
    # nfdump files aren't text files so we need to process them first
    command = f'nfdump -b -N -o csv -q -r {nfdump_file}'
    # Execute command
    result = subprocess.run(command.split(), stdout=subprocess.PIPE)
    # Get command output
    nfdump_output = result.stdout.decode('utf-8')
    input_type = 'nfdump'
    for nfdump_line in nfdump_output.splitlines():
        # this line is taken from stdout we need to remove whitespaces
        nfdump_line.replace(' ', '')
        ts = nfdump_line.split(',')[0]
        if not ts[0].isdigit():
            continue
        else:
            break

    profilerProcess = ModuleFactory().create_profiler_obj()
    sample_flow = {
        'data': nfdump_line,
    }
    profiler_detected_type: str = profilerProcess.define_separator(sample_flow, input_type)
    assert profiler_detected_type == 'nfdump'



# @pytest.mark.parametrize(
#     'file,separator,expected_value',
#     [
#         (
#             'dataset/test10-mixed-zeek-dir/conn.log',
#             '	',
#             {'dur': 9, 'proto': 7, 'state': 12},
#         )
#     ],
# )
# def test_define_columns(
#     file, separator, expected_value, mock_rdb
# ):
#     # define_columns is called on header lines
#     # line = '#fields ts      uid     id.orig_h       id.orig_p
#     # id.resp_h       id.resp_p       proto   service duration
#     # orig_bytes      resp_bytes       conn_state      local_orig
#     # local_resp      missed_bytes    history orig_pkts
#     # orig_ip_bytes   resp_pkts       resp_ip_bytes   tunnel_parents'
#     with open(file) as f:
#         while True:
#             # read from the file until you find the header
#             line = f.readline()
#             if line.startswith('#fields'):
#                 break
#     profilerProcess = ModuleFactory().create_profiler_obj()
#     line = {'data': line}
#     profilerProcess.separator = separator
#     assert profilerProcess.define_columns(line) == expected_value


# pcaps are treated as zeek files in slips, no need to test twice
# @pytest.mark.parametrize("pcap_file",[('dataset/test7-malicious.pcap')])
# def test_define_separator_pcap(pcap_file):
#     # ('dataset/test7-malicious.pcap','zeek')
#     profilerProcess = ModuleFactory().create_profilerProcess_obj(mock_db)
#
#     # pcap files aren't text files so we need to process them first
#     bro_parameter = '-r "' + pcap_file + '"'
#     command =  "zeek -C " + bro_parameter + "  tcp_inactivity_timeout=60mins local -e 'redef LogAscii::use_json=T;' -f 2>&1 > /dev/null &"
#     os.system(command)
#     # Give Zeek some time to generate at least 1 file.
#     time.sleep(3)
#
#     assert profilerProcess.define_separator(line) == 'zeek'


@pytest.mark.parametrize(
    'file,flow_type',
    [
        ('dataset/test9-mixed-zeek-dir/dns.log', 'dns'),
        ('dataset/test9-mixed-zeek-dir/conn.log', 'conn'),
        ('dataset/test9-mixed-zeek-dir/http.log', 'http'),
        ('dataset/test9-mixed-zeek-dir/ssl.log', 'ssl'),
        ('dataset/test9-mixed-zeek-dir/notice.log', 'notice'),
        # ('dataset/test9-mixed-zeek-dir/files.log', 'files.log'),
    ],
)
def test_process_line(file, flow_type):
    profiler = ModuleFactory().create_profiler_obj()
    # we're testing another functionality here
    profiler.whitelist.is_whitelisted_flow = do_nothing
    profiler.input_type = 'zeek'
    # get the class that handles the zeek input
    profiler.input_handler = SUPPORTED_INPUT_TYPES[profiler.input_type]()
    # set  the zeek json separator
    profiler.separator = SEPARATORS[profiler.input_type]

    # get zeek flow
    with open(file) as f:
        sample_flow = f.readline().replace('\n', '')

    sample_flow = json.loads(sample_flow)
    sample_flow = {
        'data': sample_flow,
        'type': flow_type
    }

    # process it
    profiler.flow = profiler.input_handler.process_line(sample_flow)
    assert profiler.flow

    # add to profile
    added_to_prof = profiler.add_flow_to_profile()
    assert added_to_prof is True

    uid = profiler.flow.uid
    profileid =  profiler.profileid
    twid =  profiler.twid

    # make sure it's added
    if flow_type == 'conn':
        added_flow = profiler.db.get_flow(uid, twid=twid)[uid]
    else:
        added_flow = (
            profiler.db.get_altflow_from_uid(profileid, twid, uid) is not None
        )
    assert added_flow is not None

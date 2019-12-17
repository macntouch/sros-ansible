# (c) 2019 Nokia
#
# Licensed under the BSD 3 Clause license
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: nokia
netconf: nokia.sros.md
short_description: Plugin to run NETCONF RPC on Nokia SR OS platform
description:
  - This Ansible plugin provides low-level abstraction APIs for executing commands
    and receiving responses via NETCONF on networking devices that run Nokia SR OS.
  - To use this plugin, please ensure that the device is running in model-driven
    mode (aka MD MODE) and has the NETCONF protocol enabled.
options:
  ncclient_device_handler:
    type: str
    default: default
    description:
      - Specifies the ncclient device-handler name for Nokia SR OS. Please refer to
        the ncclient library documentation for details.
"""

import json
import re

from ansible.module_utils._text import to_text, to_native
from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_ncclient

try:
    from ncclient import manager
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele
    HAS_NCCLIENT = True
except (ImportError, AttributeError):  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    HAS_NCCLIENT = False


class Netconf(NetconfBase):
    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    @ensure_ncclient
    def get_device_info(self):
        device_info = dict()
        device_info['network_os'] = 'sros'

        xmlns = "urn:nokia.com:sros:ns:yang:sr:state"
        f = '<state xmlns="%s"><system><platform/><bootup/><version/><lldp/></system></state>' % xmlns
        reply = to_ele(self.m.get(filter=('subtree', f)).data_xml)

        device_info['network_os_hostname'] = reply.findtext('.//{%s}state/{*}system/{*}lldp/{*}system-name' % xmlns)
        device_info['network_os_version'] = reply.findtext('.//{%s}state/{*}system/{*}version/{*}version-number' % xmlns)
        device_info['network_os_model'] = reply.findtext('.//{%s}state/{*}system/{*}platform' % xmlns)
        device_info['network_os_platform'] = 'Nokia 7x50'
        return device_info

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'netconf'
        result['device_info'] = self.get_device_info()
        result['server_capabilities'] = [c for c in self.m.server_capabilities]
        result['client_capabilities'] = [c for c in self.m.client_capabilities]
        result['session_id'] = self.m.session_id
        result['device_operations'] = self.get_device_operations(result['server_capabilities'])
        return json.dumps(result)

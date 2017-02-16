import json
import os

import sys

from l1_driver_resource_info import L1DriverResourceInfo
from l1_handler_base import L1HandlerBase
from polatis_cli_connection import PolatisCliConnection, PolatisDefaultCommandMode, PolatisEnableCommandMode, PolatisConfigCommandMode


class PolatisL1Handler(L1HandlerBase):
    
    def __init__(self, logger):
        self._logger = logger

        self._host = None
        self._username = None
        self._password = None
        self._port = None

        self._switch_family = None
        self._blade_family = None
        self._port_family = None
        self._switch_model = None
        self._blade_model = None
        self._port_model = None
        self._blade_name_template = None
        self._port_name_template = None

        self._connection = None

    def login(self, address, username, password):
        """
        :param address: str
        :param username: str
        :param password: str
        :return: None
        """
        self._host = address
        self._username = username
        self._password = password

        try:
            with open(os.path.join(os.path.dirname(sys.argv[0]), 'polatis_runtime_configuration.json')) as f:
                o = json.loads(f.read())
        except Exception as e:
            self._logger.warn('Failed to read JSON config file: ' + str(e))
            o = {}

        self._port = o.get("common_variable", {}).get("connection_port", 22)
        PolatisDefaultCommandMode.PROMPT_REGEX = o.get("common_variable", {}).get("default_prompt", r'>\s*$')
        PolatisEnableCommandMode.PROMPT_REGEX = o.get("common_variable", {}).get("enable_prompt", r'#\s*$')
        PolatisConfigCommandMode.PROMPT_REGEX = o.get("common_variable", {}).get("config_prompt", r'[(]config.*[)]#\s*$')

        self._switch_family, self._blade_family, self._port_family = o.get("common_variable", {}).get("resource_family_name",
            ['L1 Optical Switch', 'L1 Optical Switch Blade', 'L1 Optical Switch Port'])
        self._switch_model, self._blade_model, self._port_model = o.get("common_variable", {}).get("resource_model_name",
            ['Polatis', 'Blade Polatis', 'Port Polatis'])
        _, self._blade_name_template, self._port_name_template = o.get("common_variable", {}).get("resource_name",
            ['Unused', 'Blade {address}', 'Port {address}'])

        self._logger.info('Connecting to %s on port %d with username %s' % (self._host, self._port, self._username))

        self._example_driver_setting = o.get("driver_variable", {}).get("example_driver_setting", False)

        self._logger.info('Connecting...')
        cli_type = 'tl1'
        self._connection = PolatisCliConnection(self._logger, cli_type, self._host, self._port, self._username, self._password)
        self._logger.info('Connected')

    def logout(self):
        """
        :return: None
        """
        self._logger.info('Disconnecting...')
        self._connection = None
        self._logger.info('Disconnected')

    def get_resource_description(self, address):
        """
        :param address: str: root address
        :return: L1DriverResourceInfo
        """

        psize = self._connection.command("RTRV-EQPT:{name}:SYSTEM:{counter}:::PARAMETER=SIZE;")
        m = re.search(r'SYSTEM:SIZE=(?P<a>\d+)x(?P<b>\d+)', psize)
        if m:
            size1 = int(m.groupdict()['a'])
            size2 = int(m.groupdict()['b'])
            size = size1 + size2
        else:
            raise Exception('Unable to determine system size: %s' % psize)

        pserial = self._connection.command("RTRV-INV:{name}:OCS:{counter}:;")
        m = re.search(r'SN=(\w+)', pserial)
        if m:
            serial = m.groups()[0]
        else:
            self._logger.warn('Failed to extract serial number: %s' % pserial)
            serial = '-1'

        sw = L1DriverResourceInfo('', address, self._switch_family, self._switch_model, serial=serial)

        netype = self._connection.command('RTRV-NETYPE:{name}::{counter}:;')
        m = re.search(r'"(?P<vendor>.*),(?P<model>.*),(?P<type>.*),(?P<version>.*)"', netype)
        if not m:
            m = re.search(r'(?P<vendor>.*),(?P<model>.*),(?P<type>.*),(?P<version>.*)', netype)
        if m:
            sw.set_attribute('Vendor', m.groupdict()['vendor'])
            sw.set_attribute('Hardware Type', m.groupdict()['type'])
            sw.set_attribute('Version', m.groupdict()['version'])
            sw.set_attribute('Model', m.groupdict()['model'])
        else:
            self._logger.warn('Unable to parse system info: %s' % netype)

        portaddr2partneraddr = {}
        patch = self._connection.command("RTRV-PATCH:{name}::{counter}:;")
        for line in patch.split('\n'):
            line = line.strip()
            m = re.search(r'"(\d+),(\d+)"', line)
            if m:
                a = int(m.groups()[0])
                b = int(m.groups()[1])
                portaddr2partneraddr[a] = b
                portaddr2partneraddr[b] = a

        portaddr2status = {}
        shutters = self._connection.command("RTRV-PORT-SHUTTER:{name}:1&&%d:{counter}:;" % size)
        for line in shutters.split('\n'):
            line = line.strip()
            m = re.search(r'"(\d+):(\S+)"', line)
            if m:
                portaddr2status[int(m.groups()[0])] = m.groups()[1]

        for portaddr in range(1, size+1):
            if portaddr in portaddr2partneraddr:
                mappath = '%s/%d' % (address, portaddr2partneraddr[portaddr])
            else:
                mappath = None
            p = L1DriverResourceInfo('Port %0.4d' % portaddr,
                                     '%s/%d' % (address, portaddr),
                                     self._port_family,
                                     self._port_model,
                                     map_path=mappath,
                                     serial='%s.%d' % (serial, portaddr))
            p.set_attribute('State', 0 if portaddr2status.get(portaddr, 'open').lower() == 'open' else 1, typename='Lookup')
            p.set_attribute('Protocol Type', 0, typename='Lookup')
            sw.add_subresource(p)

        self._logger.info('get_resource_description returning xml: [[[' + sw.to_string() + ']]]')
        return sw

    def map_uni(self, src_port, dst_port):
        """
        :param src_port: str: source port resource full address separated by '/'
        :param dst_port: str: destination port resource full address separated by '/'
        :return: None
        """
        self._logger.info('map_uni {} {}'.format(src_port, dst_port))

        raise Exception('map_uni not implemented')

    def map_bidi(self, src_port, dst_port, mapping_group_name):
        """
        :param src_port: str: source port resource full address separated by '/'
        :param dst_port: str: destination port resource full address separated by '/'
        :param mapping_group_name: str
        :return: None
        """
        self._logger.info('map_bidi {} {} group={}'.format(src_port, dst_port, mapping_group_name))

        min_port = min(int(src_port.split('/')[-1]), int(dst_port.split('/')[-1]))
        max_port = max(int(src_port.split('/')[-1]), int(dst_port.split('/')[-1]))
        self._connection.tl1_command("ENT-PATCH:{name}:%d,%d:{counter}:;" % (min_port, max_port))

    def map_clear_to(self, src_port, dst_port):
        """
        :param src_port: str: source port resource full address separated by '/'
        :param dst_port: str: destination port resource full address separated by '/'
        :return: None
        """
        self._logger.info('map_clear_to {} {}'.format(src_port, dst_port))

        min_port = min(int(src_port.split('/')[-1]), int(dst_port.split('/')[-1]))

        self._connection.tl1_command("DLT-PATCH:{name}:%d:{counter}:;" % min_port)

    def map_clear(self, src_port, dst_port):
        """
        :param src_port: str: source port resource full address separated by '/'
        :param dst_port: str: destination port resource full address separated by '/'
        :return: None
        """
        self._logger.info('map_clear {} {}'.format(src_port, dst_port))

        self.map_clear_to(src_port, dst_port)

    def set_speed_manual(self, src_port, dst_port, speed, duplex):
        """
        :param src_port: str: source port resource full address separated by '/'
        :param dst_port: str: destination port resource full address separated by '/'
        :param speed: str
        :param duplex: str
        :return: None
        """
        self._logger.info('set_speed_manual {} {} {} {}'.format(src_port, dst_port, speed, duplex))

    def set_state_id(self, state_id):
        """
        :param state_id: str
        :return: None
        """
        self._logger.info('set_state_id {}'.format(state_id))

    def get_attribute_value(self, address, attribute_name):
        """
        :param address: str
        :param attribute_name: str
        :return: str
        """
        self._logger.info('get_attribute_value {} {} -> "fakevalue"'.format(address, attribute_name))
        return 'fakevalue'

    def get_state_id(self):
        """
        :return: str
        """
        self._logger.info('get_state_id')
        return '-1'


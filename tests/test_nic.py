# Copyright 2015-2017 ProfitBricks GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from helpers import configuration
from helpers.resources import resource
from profitbricks.client import ProfitBricksService
from profitbricks.client import Datacenter, Server, LAN, NIC
from profitbricks.errors import PBError, PBNotFoundError
from six import assertRegex


class TestNic(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.resource = resource()
        self.client = ProfitBricksService(
            username=configuration.USERNAME,
            password=configuration.PASSWORD,
            headers=configuration.HEADERS)

        # Create test datacenter.
        self.datacenter = self.client.create_datacenter(
            datacenter=Datacenter(**self.resource['datacenter']))
        self.client.wait_for_completion(self.datacenter)

        # Create test LAN.
        self.lan = self.client.create_lan(
            datacenter_id=self.datacenter['id'],
            lan=LAN(name=self.resource['lan']['name'], public=False))
        self.client.wait_for_completion(self.lan)

        # Create test server.
        self.server = self.client.create_server(
            datacenter_id=self.datacenter['id'],
            server=Server(**self.resource['server']))
        self.client.wait_for_completion(self.server)

        # Create test NIC1.
        nic1 = NIC(**self.resource['nic'])
        nic1.lan = self.lan['id']
        self.ips = ['10.0.0.1']
        nic1.ips = self.ips
        self.nic1 = self.client.create_nic(
            datacenter_id=self.datacenter['id'],
            server_id=self.server['id'],
            nic=nic1)
        self.client.wait_for_completion(self.nic1)

        # Create test NIC2.
        nic2 = NIC(**self.resource['nic'])
        nic2.lan = self.lan['id']
        self.nic2 = self.client.create_nic(
            datacenter_id=self.datacenter['id'],
            server_id=self.server['id'],
            nic=nic2)
        self.client.wait_for_completion(self.nic2)

    @classmethod
    def tearDownClass(self):
        self.client.delete_datacenter(datacenter_id=self.datacenter['id'])

    def test_list_nics(self):
        nics = self.client.list_nics(
            datacenter_id=self.datacenter['id'],
            server_id=self.server['id'])

        self.assertGreater(len(nics), 0)
        self.assertIn(nics['items'][0]['id'], (self.nic1['id'], self.nic2['id']))
        self.assertEqual(nics['items'][0]['type'], 'nic')

    def test_get_nic(self):
        nic = self.client.get_nic(datacenter_id=self.datacenter['id'],
                                  server_id=self.server['id'],
                                  nic_id=self.nic1['id'])

        self.assertEqual(nic['type'], 'nic')
        self.assertEqual(nic['id'], self.nic1['id'])
        assertRegex(self, nic['id'], self.resource['uuid_match'])
        self.assertEqual(nic['properties']['name'], self.resource['nic']['name'])
        self.assertEqual(nic['properties']['firewallActive'],
                         self.resource['nic']['firewall_active'])
        self.assertIsInstance(nic['properties']['ips'], list)
        self.assertEqual(nic['properties']['dhcp'], self.resource['nic']['dhcp'])
        self.assertEqual(nic['properties']['nat'], self.resource['nic']['nat'])
        self.assertEqual(nic['properties']['lan'], self.resource['nic']['lan'])

    def test_delete_nic(self):
        nic2 = self.client.delete_nic(datacenter_id=self.datacenter['id'],
                                      server_id=self.server['id'],
                                      nic_id=self.nic2['id'])

        self.assertTrue(nic2)

    def test_update_nic(self):
        nic = self.client.update_nic(
            datacenter_id=self.datacenter['id'],
            server_id=self.server['id'],
            nic_id=self.nic1['id'],
            name=self.resource['nic']['name'] + ' - RENAME')

        self.assertEqual(nic['id'], self.nic1['id'])
        self.assertEqual(nic['type'], 'nic')
        self.assertEqual(nic['properties']['name'], self.resource['nic']['name'] + ' - RENAME')

    def test_create_nic(self):
        self.assertEqual(self.nic1['type'], 'nic')
        self.assertEqual(self.nic1['properties']['name'], self.resource['nic']['name'])
        self.assertEqual(self.nic1['properties']['firewallActive'],
                         self.resource['nic']['firewall_active'])
        self.assertIsInstance(self.nic1['properties']['ips'], list)
        self.assertEqual(self.nic1['properties']['dhcp'], self.resource['nic']['dhcp'])
        self.assertIsNone(self.nic1['properties']['nat'])
        self.assertEqual(str(self.nic1['properties']['lan']), self.lan['id'])

    def test_get_failure(self):
        try:
            self.client.get_nic(
                datacenter_id=self.datacenter['id'],
                server_id=self.server['id'],
                nic_id='00000000-0000-0000-0000-000000000000')
        except PBNotFoundError as e:
            self.assertIn(self.resource['not_found_error'], e.content[0]['message'])

    def test_create_failure(self):
        try:
            nic = NIC(name=self.resource['nic']['name'])
            self.client.create_nic(
                datacenter_id=self.datacenter['id'],
                server_id=self.server['id'],
                nic=nic)
        except PBError as e:
            self.assertIn(self.resource['missing_attribute_error'] % 'lan',
                          e.content[0]['message'])


if __name__ == '__main__':
    unittest.main()

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# TODO(prmtl): use unittest2
import unittest

import requests_mock

from fuel_plugin.ostf_adapter import config
from fuel_plugin.ostf_adapter import mixins


CLUSTER = {
    'cluster_meta': {
        'release_id': 3,
        'mode': 'ha'
    },
    'release_data': {
        'operating_system': 'rhel'
    },
    'cluster_attributes': {
        'editable': {
            'additional_components': {
                'murano': {
                    'value': True
                },
                'sahara': {
                    'value': False
                }
            },
            'common': {}
        }
    }
}


class TestDeplTagsGetter(unittest.TestCase):

    def setUp(self):
        config.init_config([])

    def test_get_cluster_depl_tags(self):
        expected = {
            'cluster_id': 3,
            'depl_tags': set(
                ['ha', 'rhel', 'additional_components',
                 'murano', 'nova_network', 'public_on_all_nodes']
            )
        }

        with requests_mock.Mocker() as m:
            m.register_uri('GET', '/api/clusters/3',
                           json=CLUSTER['cluster_meta'])
            m.register_uri('GET', '/api/clusters/3/attributes',
                           json=CLUSTER['cluster_attributes'])
            m.register_uri('GET', '/api/releases/3',
                           json=CLUSTER['release_data'])
            res = mixins._get_cluster_depl_tags(expected['cluster_id'])

        self.assertEqual(res, expected['depl_tags'])

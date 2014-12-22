#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import bottle

from fuel_plugin.testing.tests import base


@bottle.route('/')
def index():
    return 'ok'


@bottle.route('/api/clusters/<id:int>')
def serve_cluster_meta(id):
    return base.CLUSTERS[id]['cluster_meta']


@bottle.route('/api/releases/<id:int>')
def serve_cluster_release_info(id):
    return base.CLUSTERS[id]['release_data']


@bottle.route('/api/clusters/<id:int>/attributes')
def serve_cluster_attributes(id):
    return base.CLUSTERS[id]['cluster_attributes']


bottle.run(host='localhost', port=8000, debug=True)

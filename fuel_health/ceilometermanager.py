#!/usr/bin/env python
# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import logging
import traceback

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test

LOG = logging.getLogger(__name__)


class CeilometerBaseTest(fuel_health.nmanager.NovaNetworkScenarioTest):

    @classmethod
    def setUpClass(cls):
        super(CeilometerBaseTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.wait_interval = cls.config.compute.build_interval
            cls.wait_timeout = cls.config.compute.build_timeout
            cls.private_net = 'net04'
            cls.objects_for_delete = []
            cls.nova_notifications = ['memory', 'vcpus', 'disk.root.size',
                                      'disk.ephemeral.size']
            cls.neutron_network_notifications = ['network', 'network.create',
                                                 'network.update']
            cls.neutron_subnet_notifications = ['subnet', 'subnet.create',
                                                'subnet.update']
            cls.neutron_port_notifications = ['port', 'port.create',
                                              'port.update']
            cls.neutron_router_notifications = ['router', 'router.create',
                                                'router.update']
            cls.neutron_floatingip_notifications = ['ip.floating.create',
                                                    'ip.floating.update']
            cls.glance_notifications = ['image.update', 'image.upload',
                                        'image.delete', 'image.download',
                                        'image.serve']
            cls.volume_notifications = ['volume', 'volume.size']
            cls.glance_notifications = ['image', 'image.size', 'image.update',
                                        'image.upload']
            cls.swift_notifications = ['storage.objects.incoming.bytes',
                                       'storage.objects.outgoing.bytes',
                                       'storage.api.request']
            cls.heat_notifications = ['stack.create', 'stack.update',
                                      'stack.delete', 'stack.resume',
                                      'stack.suspend']
            cls.keystone_user_notifications = [
                'identity.user.created', 'identity.user.deleted',
                'identity.user.updated']
            cls.keystone_role_notifications = [
                'identity.role.created', 'identity.role.updated',
                'identity.role.deleted']
            cls.keystone_role_assignment_notifications = [
                'identity.role_assignment.created',
                'identity.role_assignment.deleted']
            cls.keystone_project_notifications = [
                'identity.project.created', 'identity.project.updated',
                'identity.project.deleted']
            cls.keystone_group_notifications = [
                'identity.group.created', 'identity.group.updated',
                'identity.group.deleted']
            cls.keystone_trust_notifications = [
                'identity.OS-TRUST:trust.created',
                'identity.OS-TRUST:trust.deleted']

    def setUp(self):
        super(CeilometerBaseTest, self).setUp()
        self.check_clients_state()
        if not self.ceilometer_client:
            self.skipTest('Ceilometer is unavailable.')
        if not self.config.compute.compute_nodes \
                and self.config.compute.libvirt_type != 'vcenter':
            self.skipTest('There are no compute nodes')

    def create_alarm(self, **kwargs):
        """
        This method provides creation of alarm
        """
        if 'name' in kwargs:
            kwargs['name'] = rand_name(kwargs['name'])
        alarm = self.ceilometer_client.alarms.create(**kwargs)
        self.objects_for_delete.append((self.ceilometer_client.alarms.delete,
                                        alarm.alarm_id))
        return alarm

    def get_state(self, alarm_id):
        """
        This method provides getting state
        """
        return self.ceilometer_client.alarms.get_state(alarm_id=alarm_id)

    def verify_state(self, alarm_id, state):
        """
        This method provides getting state
        """
        alarm_state_resp = self.get_state(alarm_id)
        if not alarm_state_resp == state:
            self.fail('State was not setted')

    def wait_for_instance_status(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    def wait_for_alarm_status(self, alarm_id, status=None):
        """
        The method is a customization of test.status_timeout().
        """

        def check_status():
            alarm_state_resp = self.get_state(alarm_id)
            if status:
                if alarm_state_resp == status:
                    return True
            elif alarm_state_resp == 'alarm' or 'ok':
                return True  # All good.
            LOG.debug("Waiting for state to get alarm status.")

        if not fuel_health.test.call_until_true(check_status, 1000, 10):
            actual_status = self.get_state(alarm_id)
            self.fail(
                "Timed out waiting to become alarm status. "
                "Expected status:{exp_status}; "
                "Actual status:{act_status}".format(
                    exp_status=status if status else "'alarm' or 'ok'",
                    act_status=actual_status))

    def wait_for_sample_of_metric(self, metric, query=None, limit=100):
        """
        This method is to wait for sample to add it to database.
        query example:
        query=[
        {'field':'resource',
        'op':'eq',
        'value':'000e6838-471b-4a14-8da6-655fcff23df1'
        }]
        """

        def check_status():
            body = self.ceilometer_client.samples.list(meter_name=metric,
                                                       q=query, limit=limit)
            if body:
                return True

        if fuel_health.test.call_until_true(check_status, 600, 10):
            return self.ceilometer_client.samples.list(meter_name=metric,
                                                       q=query, limit=limit)
        else:
            self.fail("Timed out waiting to become sample for metric:{metric}"
                      " with query:{query}".format(metric=metric,
                                                   query=query))

    def wait_for_statistic_of_metric(self, meter_name, query=None,
                                     period=None):
        """
        The method is a customization of test.status_timeout().
        """

        def check_status():
            stat_state_resp = self.ceilometer_client.statistics.list(
                meter_name, q=query, period=period)
            if len(stat_state_resp) > 0:
                return True  # All good.
            LOG.debug("Waiting for while metrics will available.")

        if not fuel_health.test.call_until_true(check_status, 600, 10):

            self.fail("Timed out waiting to become alarm")
        else:
            return self.ceilometer_client.statistics.list(meter_name, q=query,
                                                          period=period)

    def wait_notifications(self, notification_list, query):
        for sample in notification_list:
            self.wait_for_sample_of_metric(sample, query)

    def wait_samples_count(self, sample, query, count):

        def check_count():
            samples = self.ceilometer_client.samples.list(sample, q=query)
            return len(samples) > count

        if not fuel_health.test.call_until_true(check_count, 60, 1):
            self.fail('Count of samples list isn\'t '
                      'greater than expected value')

    def identity_helper(self):
        user_pass = rand_name("ceilo-user-pass")
        user_name = rand_name("ceilo-user-update")
        tenant_name = rand_name("ceilo-tenant-update")
        tenant = self.identity_client.tenants.create(rand_name("ceilo-tenant"))
        self.objects_for_delete.append((self.identity_client.tenants.delete,
                                       tenant))
        self.identity_client.tenants.update(tenant.id, name=tenant_name)
        user = self.identity_client.users.create(rand_name("ceilo-user"),
                                                 user_pass, tenant.id)
        self.objects_for_delete.append((self.identity_client.users.delete,
                                       user))
        self.identity_client.users.update(user, name=user_name)
        role = self.identity_v3_client.roles.create(rand_name("ceilo-role"))
        self.identity_v3_client.roles.update(role, user=user.id,
                                             project=tenant.id)
        self.identity_v3_client.roles.grant(role, user=user.id,
                                            project=tenant.id)
        self.objects_for_delete.append((self.identity_client.roles.delete,
                                       role))
        user_client = self.manager_class()._get_identity_client(user_name,
                                                                user_pass,
                                                                tenant_name, 3)
        trust = user_client.trusts.create(self.identity_v3_client.user_id,
                                          user.id, [role.name], tenant.id)
        self.objects_for_delete.append((user_client.trusts.delete,
                                       trust))
        group = self.identity_v3_client.groups.create(rand_name("ceilo-group"))
        self.objects_for_delete.append((self.identity_v3_client.groups.delete,
                                        group))
        self.identity_v3_client.groups.update(
            group, name=rand_name("ceilo-group-update"))
        self.identity_v3_client.groups.delete(group)
        user_client.trusts.delete(trust)
        self.identity_client.roles.delete(role)
        self.identity_client.users.delete(user)
        self.identity_client.tenants.delete(tenant)
        return tenant, user, role, group, trust

    @staticmethod
    def cleanup_resources(object_list):
        for method, resource in object_list:
            try:
                method(resource)
            except Exception:
                LOG.debug(traceback.format_exc())

    @classmethod
    def tearDownClass(cls):
        if cls.manager.clients_initialized:
            cls.cleanup_resources(cls.objects_for_delete)
        super(CeilometerBaseTest, cls).tearDownClass()

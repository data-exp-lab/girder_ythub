#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httmock
from tests import base
from girder.models.model_base import ValidationException


def setUpModule():
    base.enabledPlugins.append('ythub')
    base.startServer()


def tearDownModule():
    base.stopServer()


class FrontendTestCase(base.TestCase):

    def _getUser(self, userDict):
        try:
            user = self.model('user').createUser(**userDict)
        except ValidationException:
            resp = self.request(
                path='/user/authentication', method='GET',
                basicAuth='{login}:{password}'.format(**userDict))
            self.assertStatusOk(resp)
            user = resp.json['user']
        return user

    def setUp(self):
        global PluginSettings
        from girder.plugins.ythub.constants import PluginSettings
        self.model('setting').set(
            PluginSettings.TMPNB_URL, "https://tmpnb.null")

        users = ({
            'email': 'root@dev.null',
            'login': 'admin',
            'firstName': 'Root',
            'lastName': 'van Klompf',
            'password': 'secret',
            'admin': True,
        }, {
            'email': 'joe@dev.null',
            'login': 'joeregular',
            'firstName': 'Joe',
            'lastName': 'Regular',
            'password': 'secret',
            'admin': False,
        })
        self.admin, self.user = [self._getUser(user) for user in users]

    @httmock.all_requests
    def mockOtherRequest(self, url, request):
        raise Exception('Unexpected url %s' % str(request.url))

    def testFrontends(self):
        example_frontend = {
            'imageName': 'xarthisius/ythub',
            'command': './perform_magic',
            'memLimit': '2048m',
            'port': 12345,
            'user': 'user',
            'targetMount': '/foo',
            'description': 'foo',
            'cpuShares': None,
            'public': False,
        }

        # Initially there are no frontends
        resp = self.request('/frontend', method='GET', params={})
        self.assertStatus(resp, 200)
        self.assertEqual(resp.json, [])

        # Try to create frontend with invalid imageName
        resp = self.request(
            path='/frontend', method='POST', params={'imageName': 'blah^hhlh',
                                                     'targetMount': '/foo'},
            user=self.admin)
        self.assertValidationError(resp, 'imageName')

        # Try to create frontend as regular user
        resp = self.request(
            path='/frontend', method='POST', params=example_frontend,
            user=self.user)
        self.assertStatus(resp, 403)

        # Actually create a new frontend (private)
        resp = self.request(
            path='/frontend', method='POST', params=example_frontend,
            user=self.admin)
        self.assertStatus(resp, 200)
        frontend = resp.json

        # Verify that user does not see private frontend
        resp = self.request(
            path='/frontend', method='GET', params={}, user=self.user)
        self.assertStatus(resp, 200)
        self.assertEqual(resp.json, [])

        # Verify that admin sees private frontend
        resp = self.request(
            path='/frontend', method='GET', params={}, user=self.admin)
        self.assertStatus(resp, 200)
        self.assertEqual(resp.json[0]['_id'], frontend['_id'])

        # Update frontend and make it public
        resp = self.request(
            path='/frontend/{_id}'.format(**frontend), method='PUT',
            params={'public': True, 'memLimit': '1024m'}, user=self.admin)
        self.assertStatus(resp, 200)
        self.assertEqual(resp.json['_id'], frontend['_id'])
        self.assertEqual(resp.json['public'], True)
        self.assertEqual(resp.json['memLimit'], '1024m')

        # Verify that anyone can see public frontend
        resp = self.request(
            path='/frontend/{_id}'.format(**frontend), method='GET',
            user=self.user)
        self.assertStatus(resp, 200)
        self.assertEqual(resp.json['_id'], frontend['_id'])

        # Verify that user cannot remove the frontend
        resp = self.request(
            path='/frontend/{_id}'.format(**frontend), method='DELETE',
            user=self.user)
        self.assertStatus(resp, 403)

        # Actually remove the frontend
        resp = self.request(
            path='/frontend/{_id}'.format(**frontend), method='DELETE',
            user=self.admin)
        self.assertStatus(resp, 200)

        # Verify that the frontend is gone
        resp = self.request(
            path='/frontend/{_id}'.format(**frontend), method='GET',
            user=self.user)
        self.assertStatus(resp, 400)

    def tearDown(self):
        self.model('user').remove(self.user)
        self.model('user').remove(self.admin)

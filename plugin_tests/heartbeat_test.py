#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import httmock
import json
import pytz
import six
import time
from tests import base

from girder.models.model_base import ValidationException


def setUpModule():
    base.enabledPlugins.append('ythub')
    base.startServer()


def tearDownModule():
    base.stopServer()


class NotebookCullingTestCase(base.TestCase):

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
        self.model('setting').set(
            PluginSettings.CULLING_PERIOD, 3.0 / 3600.0)
        self.model('setting').set(
            PluginSettings.CULLING_FREQUENCY, 1.0 / 3600.0)

        users = ({
            'email': 'root@dev.null',
            'login': 'admin',
            'firstName': 'Root',
            'lastName': 'van Klompf',
            'password': 'secret'
        }, {
            'email': 'joe@dev.null',
            'login': 'joeregular',
            'firstName': 'Joe',
            'lastName': 'Regular',
            'password': 'secret'
        })
        self.admin, self.user = [self._getUser(user) for user in users]
        now = datetime.datetime.utcnow()
        self.now = now.replace(tzinfo=pytz.UTC).isoformat()

    @httmock.all_requests
    def mockOtherRequest(self, url, request):
        raise Exception('Unexpected url %s' % str(request.url))

    def testNotebooks(self):
        tmpnb_response = {
            'mountPoint': '/var/lib/blah',
            'containerId': '123456',
            'containerPath': '/user/blah',
            'host': '172.168.1.16'
        }

        # Grab the default user folders
        resp = self.request(
            path='/folder', method='GET', user=self.user, params={
                'parentType': 'user',
                'parentId': self.user['_id'],
                'sort': 'name',
                'sortdir': 1
            })
        privateFolder = resp.json[0]
        publicFolder = resp.json[1]

        example_frontend = {
            'imageName': 'xarthisius/ythub',
            'command': './perform_magic',
            'memLimit': '2048m',
            'port': 12345,
            'user': 'user',
            'description': 'foo',
            'cpuShares': None,
            'public': True,
        }
        # Actually create a new frontend (private)
        resp = self.request(
            path='/frontend', method='POST', params=example_frontend,
            user=self.admin)
        self.assertStatus(resp, 200)
        frontend = resp.json

        @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                          path='^/$', method='GET')
        def mockTmpnbHubGet(url, request):
            return json.dumps({notebook['containerId']: self.now})

        @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                          path='^/$', method='POST')
        def mockTmpnbHubPost(url, request):
            try:
                params = json.loads(request.body.decode('utf8'))
                self.assertIn(
                    params['folderId'], (str(privateFolder['_id']),
                                         str(publicFolder['_id'])))
                self.assertEqual(
                    params['frontendId'], str(frontend['_id']))
            except (KeyError, AssertionError) as e:
                return json.dumps({
                    'status_code': 401,
                    'content': json.dumps({'error': repr(e)})
                })

            return json.dumps(tmpnb_response)

        @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                          path='^/$', method='DELETE')
        def mockTmpnbHubDelete(url, request):
            try:
                params = json.loads(request.body.decode('utf8'))
                self.assertEqual(
                    params['folderId'], str(privateFolder['_id']))
                for k, v in six.viewitems(tmpnb_response):
                    self.assertEqual(params[k], v)
                self.assertEqual(request.headers['docker-host'],
                                 tmpnb_response['host'])
                self.assertEqual(request.headers['content-type'],
                                 tmpnb_response['application/json'])
            except (KeyError, AssertionError) as e:
                return json.dumps({
                    'status_code': 401,
                    'content': json.dumps({'error': repr(e)})
                })

            return None

        with httmock.HTTMock(mockTmpnbHubPost, self.mockOtherRequest):
            params = {
                'frontendId': str(frontend['_id']),
                'folderId': str(privateFolder['_id'])
            }
            resp = self.request(
                '/notebook', method='POST',
                user=self.user, params=params)
            self.assertStatus(resp, 200)
            notebook = resp.json

        with httmock.HTTMock(mockTmpnbHubDelete, mockTmpnbHubGet,
                             self.mockOtherRequest):
            startTime = time.time()
            while True:
                resp = self.request(
                    path='/notebook/{_id}'.format(**notebook), method='GET',
                    user=self.user)
                if resp.status == 400:
                    break
                if time.time() - startTime > 10:
                    break
                time.sleep(0.5)
        resp = self.request(
            path='/notebook/{_id}'.format(**notebook), method='GET',
            user=self.user)
        self.assertStatus(resp, 400)

    def tearDown(self):
        self.model('user').remove(self.user)
        self.model('user').remove(self.admin)

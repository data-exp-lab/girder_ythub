#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httmock
import json
import six
from tests import base
from girder.models.model_base import ValidationException


def setUpModule():
    base.enabledPlugins.append('ythub')
    base.startServer()


def tearDownModule():
    base.stopServer()


class NotebookTestCase(base.TestCase):

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
            'password': 'secret'
        }, {
            'email': 'joe@dev.null',
            'login': 'joeregular',
            'firstName': 'Joe',
            'lastName': 'Regular',
            'password': 'secret'
        })
        self.admin, self.user = [self._getUser(user) for user in users]

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
                          path='^/$', method='POST')
        def mockTmpnbHubPost(url, request):
            try:
                params = json.loads(request.body.decode('utf8'))
                self.assertEqual(
                    params['folderId'], str(privateFolder['_id']))
                self.assertEqual(
                    params['frontendId'], str(frontend['_id']))
            except (KeyError, AssertionError) as e:
                return json.dumps({
                    'status_code': 401,
                    'content': json.dumps({'error': repr(e)})
                })

            return json.dumps(tmpnb_response)

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
        self.assertEqual(notebook['host'], tmpnb_response['host'])
        self.assertEqual(notebook['mountPoint'], tmpnb_response['mountPoint'])
        self.assertEqual(notebook['containerId'], tmpnb_response['containerId'])
        self.assertEqual(notebook['containerPath'], tmpnb_response['containerPath'])
        self.assertEqual(notebook['folderId'], str(privateFolder['_id']))
        self.assertEqual(notebook['userId'], str(self.user['_id']))

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

        with httmock.HTTMock(mockTmpnbHubDelete, self.mockOtherRequest):
            resp = self.request(
                '/notebook/{_id}'.format(**notebook), method='DELETE',
                user=self.user)
            self.assertStatus(resp, 200)
        
        # Actually remove the frontend 
        resp = self.request(
            path='/frontend/{_id}'.format(**frontend), method='DELETE',
            user=self.admin)

    def tearDown(self):
        self.model('user').remove(self.user)
        self.model('user').remove(self.admin)

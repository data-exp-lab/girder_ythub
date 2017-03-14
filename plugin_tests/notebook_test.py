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
        self.assertEqual(notebook['containerId'],
                         tmpnb_response['containerId'])
        self.assertEqual(notebook['containerPath'],
                         tmpnb_response['containerPath'])
        self.assertEqual(notebook['folderId'], str(privateFolder['_id']))
        self.assertEqual(notebook['userId'], str(self.user['_id']))

        with httmock.HTTMock(mockTmpnbHubPost, self.mockOtherRequest):
            params = {
                'frontendId': str(frontend['_id']),
                'folderId': str(privateFolder['_id'])
            }
            # Return exisiting
            resp = self.request(
                path='/notebook', method='POST', user=self.user,
                params=params)
            self.assertStatus(resp, 200)
            self.assertEqual(resp.json['_id'], notebook['_id'])

            # Create 2nd user's nb
            params['folderId'] = str(publicFolder['_id'])
            resp = self.request(
                path='/notebook', method='POST', user=self.user,
                params=params)
            self.assertStatus(resp, 200)
            other_notebook = resp.json

            # Create admin nb
            params['folderId'] = str(publicFolder['_id'])
            resp = self.request(
                path='/notebook', method='POST', user=self.admin,
                params=params)
            self.assertStatus(resp, 200)
            admin_notebook = resp.json

        # By default user can list only his/her notebooks
        resp = self.request(
            path='/notebook', method='GET', user=self.user)
        self.assertStatus(resp, 200)
        self.assertEqual([_['_id'] for _ in resp.json],
                         [other_notebook['_id'], notebook['_id']])

        # Filter by folder
        resp = self.request(
            path='/notebook', method='GET', user=self.admin,
            params={'folderId': publicFolder['_id']})
        self.assertStatus(resp, 200)
        self.assertEqual([_['_id'] for _ in resp.json],
                         [admin_notebook['_id'], other_notebook['_id']])

        # Filter by folder and user
        resp = self.request(
            path='/notebook', method='GET', user=self.admin,
            params={'folderId': publicFolder['_id'],
                    'userId': self.user['_id']})
        self.assertStatus(resp, 200)
        self.assertEqual(resp.json[0]['_id'], other_notebook['_id'])

        # Get notebook by Id
        resp = self.request(
            path='/notebook/{_id}'.format(**notebook), method='GET')
        self.assertStatus(resp, 401)

        resp = self.request(
            path='/notebook/{_id}'.format(**admin_notebook), method='GET',
            user=self.user)
        self.assertStatus(resp, 403)

        resp = self.request(
            path='/notebook/{_id}'.format(**notebook), method='GET',
            user=self.admin)
        self.assertStatus(resp, 200)
        self.assertEqual(resp.json['_id'], notebook['_id'])

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

        # Delete notebooks
        with httmock.HTTMock(mockTmpnbHubDelete, self.mockOtherRequest):
            resp = self.request(
                path='/notebook/{_id}'.format(**admin_notebook),
                method='DELETE', user=self.user)
            self.assertStatus(resp, 403)

            for nb in (notebook, other_notebook, admin_notebook):
                resp = self.request(
                    path='/notebook/{_id}'.format(**nb), method='DELETE',
                    user=self.admin)
                self.assertStatus(resp, 200)

        # Check if notebook is gone
        resp = self.request(
            path='/notebook/{_id}'.format(**notebook), method='GET',
            user=self.admin)

    def tearDown(self):
        self.model('user').remove(self.user)
        self.model('user').remove(self.admin)

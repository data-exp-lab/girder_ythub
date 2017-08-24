#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock
from tests import base
from girder.models.model_base import ValidationException


def setUpModule():
    base.enabledPlugins.append('ythub')
    base.startServer()


def tearDownModule():
    base.stopServer()


class FakeAsyncResult(object):
    def __init__(self):
        self.task_id = 'fake_id'

    def get(self):
        return dict(
            nodeId='123456',
            volumeId='blah_volume',
            serviceId='tmp-blah',
            urlPath='?token=foo'
        )


class FakeAsyncResult2(object):
    def __init__(self):
        self.task_id = 'fake_id'

    def get(self):
        return dict(
            nodeId='654321',
            volumeId='foobar_volume',
            serviceId='tmp-foobar',
            urlPath='?token=blah'
        )


class FakeAsyncResult3(object):
    def __init__(self):
        self.task_id = 'fake_id'

    def get(self):
        return dict(
            nodeId='162534',
            volumeId='foobaz_volume',
            serviceId='tmp-foobaz',
            urlPath='?token=ragl'
        )


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

    def testNotebooks(self):
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
            'targetMount': '/blah',
            'urlPath': '?token={token}',
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

        with mock.patch('celery.Celery') as celeryMock:
            with mock.patch('tornado.httpclient.HTTPClient') as tornadoMock:
                instance = celeryMock.return_value
                instance.send_task.side_effect = [
                    FakeAsyncResult(), FakeAsyncResult(),
                    FakeAsyncResult2(), FakeAsyncResult2(),
                    FakeAsyncResult3(), FakeAsyncResult3(),
                    FakeAsyncResult(), FakeAsyncResult()
                ]
                req = tornadoMock.return_value
                req.fetch.return_value = {}

                params = {
                    'frontendId': str(frontend['_id']),
                    'folderId': str(privateFolder['_id'])
                }
                resp = self.request(
                    '/notebook', method='POST',
                    user=self.user, params=params)
                self.assertStatus(resp, 200)
                notebook = resp.json

        self.assertEqual(notebook['serviceInfo']['nodeId'], '123456')
        self.assertEqual(notebook['serviceInfo']['volumeId'], 'blah_volume')
        self.assertEqual(notebook['serviceInfo']['serviceId'], 'tmp-blah')
        self.assertEqual(notebook['url'], 'https://tmp-blah.0.0.1/?token=foo')
        self.assertEqual(notebook['frontendId'], str(frontend['_id']))
        self.assertEqual(notebook['folderId'], str(privateFolder['_id']))
        self.assertEqual(notebook['creatorId'], str(self.user['_id']))

        with mock.patch('celery.Celery') as celeryMock:
            with mock.patch('tornado.httpclient.HTTPClient') as tornadoMock:
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

        with mock.patch('celery.Celery') as celeryMock:
            resp = self.request(
                path='/notebook/{_id}'.format(**admin_notebook),
                method='DELETE', user=self.user)
            self.assertStatus(resp, 403)

            resp = self.request(
                path='/notebook/{_id}'.format(**notebook), method='DELETE',
                user=self.admin)
            self.assertStatus(resp, 200)

        # Check if notebook is gone
        resp = self.request(
            path='/notebook/{_id}'.format(**notebook), method='GET',
            user=self.admin)
        self.assertStatus(resp, 400)

    def tearDown(self):
        self.model('user').remove(self.user)
        self.model('user').remove(self.admin)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httmock
import json
from tests import base

# This method will be used by the mock to replace requests.post


def mocked_requests_post(*args, **kwargs):
    class MockResponse:

        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'http://someurl.com/test.json':
        return MockResponse({"key1": "value1"}, 200)
    else:
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse({}, 404)


def setUpModule():
    base.enabledPlugins.append('ythub')
    base.startServer()


def tearDownModule():
    base.stopServer()


class AssetFolderTestCase(base.TestCase):

    def setUp(self):
        global PluginSettings
        from girder.plugins.ythub.constants import PluginSettings
        self.model('setting').set(
            PluginSettings.TMPNB_URL, "https://tmpnb.null")
        self.testUser = self.model('user').createUser(
            email='bgates@microsoft.com',
            login='bgates',
            firstName='Bill',
            lastName='Gates',
            password='linuxRulez',
            admin=True
        )
        self.testFrontend = self.model('frontend', 'ythub').createFrontend(
            'xarthisius/ythub')
        self.testCollection = self.model('collection').createCollection(
            'testColl', self.testUser, public=True)
        self.testFolder = self.model('folder').createFolder(
            self.testCollection, 'testFolder', parentType='collection',
            public=True)

    @httmock.all_requests
    def mockOtherRequest(self, url, request):
        raise Exception('Unexpected url %s' % str(request.url))

    def testNotebookCreationDeletion(self):
        tmpnb_response = {
            'mountPoint': '/var/lib/blah',
            'containerId': '123456',
            'containerPath': '/user/blah',
            'host': '172.168.1.16'
        }

        @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                          path='^/$', method='POST')
        def mockTmpnbHubPost(url, request):
            try:
                params = json.loads(request.body)
                self.assertEqual(
                    params['folderId'], str(self.testFolder['_id']))
                self.assertEqual(
                    params['frontendId'], str(self.testFrontend['_id']))
            except (KeyError, AssertionError) as e:
                return json.dumps({
                    'status_code': 401,
                    'content': json.dumps({'error': repr(e)})
                })

            return json.dumps(tmpnb_response)

        with httmock.HTTMock(mockTmpnbHubPost, self.mockOtherRequest):
            params = {'frontendId': str(self.testFrontend['_id'])}
            resp = self.request(
                '/notebook/%s' % self.testFolder['_id'],
                user=self.testUser, params=params)
            self.assertStatus(resp, 200)
            notebook = resp.json
        self.assertEqual(notebook['host'], tmpnb_response['host'])
        self.assertEqual(notebook['mountPoint'], tmpnb_response['mountPoint'])
        self.assertEqual(notebook['containerId'], tmpnb_response['containerId'])
        self.assertEqual(notebook['containerPath'], tmpnb_response['containerPath'])
        self.assertEqual(notebook['folderId'], self.testFolder['_id'])
        self.assertEqual(notebook['userId'], self.testUser['_id'])

        @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                          path='^/$', method='DELETE')
        def mockTmpnbHubDelete(url, request):
            try:
                params = json.loads(request.body)
                self.assertEqual(
                    params['girder_token'], self.token)
                self.assertEqual(
                    params['folderId'], str(self.testFolder['_id']))
                self.assertEqual(
                    params['userId'], str(self.testUser['_id']))
            except (KeyError, AssertionError) as e:
                return json.dumps({
                    'status_code': 401,
                    'content': json.dumps({'error': repr(e)})
                })

            return json.dumps({'url': '/arglebargle'})

        with httmock.HTTMock(mockTmpnbHubDelete, self.mockOtherRequest):
            self.model('notebook', 'ythub').deleteNotebook(
                notebook, {'_id': self.token})
        self.model('notebook', 'ythub').remove(notebook)

    def tearDown(self):
        self.model('folder').remove(self.testFolder)
        self.model('collection').remove(self.testCollection)
        self.model('user').remove(self.testUser)

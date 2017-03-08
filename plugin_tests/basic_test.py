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
    base.enabledPlugins.append('wholetale')
    base.startServer()


def tearDownModule():
    base.stopServer()


class AssetFolderTestCase(base.TestCase):

    def setUp(self):
        global PluginSettings
        from girder.plugins.wholetale.constants import PluginSettings
        self.model('setting').set(
            PluginSettings.TMPNB_URL, "https://tmpnb.null")
        self.token = 'token'
        self.testUser = self.model('user').createUser(
            email='bgates@microsoft.com',
            login='bgates',
            firstName='Bill',
            lastName='Gates',
            password='linuxRulez',
            admin=True
        )

        self.testCollection = self.model('collection').createCollection(
            'testColl', self.testUser, public=True)
        self.testFolder = self.model('folder').createFolder(
            self.testCollection, 'testFolder', parentType='collection',
            public=True)

    @httmock.all_requests
    def mockOtherRequest(self, url, request):
        raise Exception('Unexpected url %s' % str(request.url))

    def testNotebookCreationDeletion(self):
        @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                          path='^/$', method='POST')
        def mockTmpnbHubPost(url, request):
            try:
                params = json.loads(request.body)
                self.assertEqual(
                    params['girder_token'], self.token)
                self.assertEqual(
                    params['collection_id'], str(self.testFolder['_id']))
            except (KeyError, AssertionError) as e:
                return json.dumps({
                    'status_code': 401,
                    'content': json.dumps({'error': repr(e)})
                })

            return json.dumps({'url': '/arglebargle'})

        with httmock.HTTMock(mockTmpnbHubPost, self.mockOtherRequest):
            notebook = self.model('notebook', 'wholetale').createNotebook(
                self.testFolder, self.testUser, {'_id': self.token})
        self.assertEqual(notebook['url'], '/arglebargle')
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
            self.model('notebook', 'wholetale').deleteNotebook(
                notebook, {'_id': self.token})
        self.model('notebook', 'wholetale').remove(notebook)

    def tearDown(self):
        self.model('folder').remove(self.testFolder)
        self.model('collection').remove(self.testCollection)
        self.model('user').remove(self.testUser)

import six
from tests import base
from girder.constants import SettingKey


def setUpModule():
    base.enabledPlugins.append('ythub')
    base.startServer()


def tearDownModule():
    base.stopServer()


class YtHubTestCase(base.TestCase):

    def testConfigValidators(self):
        from girder.plugins.ythub.constants import PluginSettings
        adminDef = {
            'email': 'root0@dev.null',
            'login': 'admin0',
            'firstName': 'Root0',
            'lastName': 'van Klompf0',
            'password': 'secret0',
            'admin': True
        }
        user = self.model('user').createUser(**adminDef)

        culls = {'period': PluginSettings.CULLING_PERIOD,
                 'frequency': PluginSettings.CULLING_FREQUENCY}
        for k, v in six.iteritems(culls):
            params = {
                'key': v,
                'value': 'bbb'
            }
            resp = self.request('/system/setting', user=user, method='PUT',
                                params=params)
            self.assertStatus(resp, 400)
            self.assertEqual(resp.json, {
                'field': 'value',
                'type': 'validation',
                'message': 'Culling %s must float.' % k
            })

            params = {
                'key': v,
                'value': ''
            }
            resp = self.request('/system/setting', user=user, method='PUT',
                                params=params)
            self.assertStatus(resp, 400)
            self.assertEqual(resp.json, {
                'field': 'value',
                'type': 'validation',
                'message': 'Culling %s must not be empty.' % k
            })

        resp = self.request('/system/setting', user=user, method='PUT',
                            params={'key': PluginSettings.TMPNB_URL,
                                    'value': ''})
        self.assertStatus(resp, 400)
        self.assertEqual(resp.json, {
            'field': 'value',
            'type': 'validation',
            'message': 'TmpNB URL must not be empty.'
        })

        keys = {'PUB_KEY': PluginSettings.HUB_PUB_KEY,
                'PRIV_KEY': PluginSettings.HUB_PRIV_KEY}
        for k, v in six.iteritems(keys):
            params = {
                'key': v,
                'value': ''
            }
            resp = self.request('/system/setting', user=user, method='PUT',
                                params=params)
            self.assertStatus(resp, 400)
            self.assertEqual(resp.json, {
                'field': 'value',
                'type': 'validation',
                'message': '%s must not be empty.' % k
            })

            params = {
                'key': v,
                'value': 'blah'
            }
            resp = self.request('/system/setting', user=user, method='PUT',
                                params=params)
            self.assertStatus(resp, 400)
            self.assertEqual(resp.json, {
                'type': 'validation',
                'message': "%s's data structure could not be decoded." % k
            })

    def testDefaultUserFolders(self):
        self.model('setting').set(SettingKey.USER_DEFAULT_FOLDERS,
                                  'public_private')
        user1 = self.model('user').createUser(
            'folderuser1', 'passwd', 'tst', 'usr', 'folderuser1@user.com')
        user1Folders = self.model('folder').find({
            'parentId': user1['_id'],
            'parentCollection': 'user'})
        self.assertSetEqual(
            set(folder['name'] for folder in user1Folders),
            {'Public', 'Private', 'Notebooks'}
        )

        # User should be able to see that 2 folders exist
        resp = self.request(path='/user/%s/details' % user1['_id'],
                            user=user1)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['nFolders'], 3)

        # Anonymous users should only see 1 folder exists
        resp = self.request(path='/user/%s/details' % user1['_id'])
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['nFolders'], 1)

        self.model('setting').set(SettingKey.USER_DEFAULT_FOLDERS,
                                  'none')
        user2 = self.model('user').createUser(
            'folderuser2', 'mypass', 'First', 'Last', 'folderuser2@user.com')
        user2Folders = self.model('folder').find({
            'parentId': user2['_id'],
            'parentCollection': 'user'})
        self.assertSetEqual(
            set(folder['name'] for folder in user2Folders),
            {'Notebooks'}
        )

    def testModelExtensions(self):
        user = self.model('user').createUser(
            'folderuser3', 'passwd', 'tst', 'usr', 'folderuser3@user.com')
        resp = self.request(
            path='/folder', method='GET', user=user, params={
                'parentType': 'user',
                'parentId': user['_id'],
                'sort': 'name',
                'sortdir': 1
            })
        folder = self.model('folder').load(resp.json[0]['_id'], user=user)

        resp = self.request(
            path='/folder/{_id}/rootpath'.format(**folder),
            user=user, method='GET')
        self.assertStatusOk(resp)
        self.assertEqual(
            str(user['_id']), resp.json[0]['object']['_id'])

        # not much to check
        resp = self.request(
            path='/folder/{_id}/check'.format(**folder),
            user=user, method='PUT')
        self.assertStatusOk(resp)

        resp = self.request(
            path='/item', method='POST', user=user,
            params={'name': 'blah', 'folderId': str(folder['_id'])})
        self.assertStatusOk(resp)
        item = resp.json

        resp = self.request(
            path='/item/{_id}/check'.format(**item),
            user=user, method='PUT')
        self.assertStatusOk(resp)

    def testListing(self):
        adminDef = {
            'email': 'root2@dev.null',
            'login': 'admin2',
            'firstName': 'Root2',
            'lastName': 'van Klompf2',
            'password': 'secret2',
            'admin': True
        }
        user = self.model('user').createUser(**adminDef)
        resp = self.request(
                path='/assetstore', method='POST', user=user,
                params={'type': 0, 'name': 'test', 'root': '/tmp/girder'})
        self.assertStatusOk(resp)
        assetstore = resp.json

        c1 = self.model('collection').createCollection('c1', user)
        f1 = self.model('folder').createFolder(
            c1, 'f1', parentType='collection')
        i1 = self.model('item').createItem('i1', user, f1)
        i2 = self.model('item').createItem('i2', user, f1)
        fl1 = self.model('file').createFile(user, i1, 'foo1', 7, assetstore)
        fl2 = self.model('file').createFile(user, i1, 'foo2', 13, assetstore)
        fl3 = self.model('file').createFile(user, i2, 'foo3', 19, assetstore)
        for ofile in (fl1, fl2, fl3):
            ofile['path'] = '/nonexistent/path/%s' % ofile['name']
            ofile = self.model('file').save(ofile)

        f2 = self.model('folder').createFolder(
            f1, 'f2', parentType='folder')
        i3 = self.model('item').createItem('i3', user, f2)
        self.model('file').createFile(user, i3, 'foo4', 23, assetstore)
        i4 = self.model('item').createItem('i4', user, f2)
        self.model('file').createFile(user, i4, 'foo5', 65535, assetstore)
        i5 = self.model('item').createItem('i5', user, f2)
        self.model('file').createFile(user, i5, 'foo6', 2.0 * 1024**8,
                                      assetstore)

        resp = self.request(
            path='/folder/{_id}/listing'.format(**f1), method='GET',
            user=user)
        self.assertStatusOk(resp)
        self.assertEqual(set(_['_id'] for _ in resp.json['files']),
                         set((str(fl3['_id']),)))
        self.assertEqual(set(_['_id'] for _ in resp.json['folders']),
                         set((str(f2['_id']), str(i1['_id']))))
        resp = self.request(
            path='/item/{_id}/listing'.format(**i1), method='GET',
            user=user)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['folders'], [])
        self.assertEqual(set(_['_id'] for _ in resp.json['files']),
                         set((str(fl1['_id']), str(fl2['_id']))))

        resp = self.request(
            path='/ythub/{_id}/examples'.format(**f1), method='GET',
            user=user)
        self.assertStatusOk(resp)
        result = {'f2': [
            {
                'code': 'unknown',
                'description': '',
                'filename': 'i3',
                'url': ('http://127.0.0.1/api/v1/item/'
                        '{_id}/download'.format(**i3)),
                'size': '23.0B'
            }, {
                'code': 'unknown',
                'description': '',
                'filename': 'i4',
                'url': ('http://127.0.0.1/api/v1/item/'
                        '{_id}/download'.format(**i4)),
                'size': '64.0KiB'
            }, {
                'code': 'unknown',
                'description': '',
                'filename': 'i5',
                'url': ('http://127.0.0.1/api/v1/item/'
                        '{_id}/download'.format(**i5)),
                'size': '2.0YiB'
            }
        ]}
        self.assertEqual(resp.json, result)

    def testHubRoutes(self):
        from girder.plugins.ythub.constants import PluginSettings
        self.model('setting').set(
            PluginSettings.TMPNB_URL, 'https://tmpnb.null')
        adminDef = {
            'email': 'root@dev.null',
            'login': 'admin',
            'firstName': 'Root',
            'lastName': 'van Klompf',
            'password': 'secret',
            'admin': True
        }
        admin = self.model('user').createUser(**adminDef)

        resp = self.request(path='/ythub/genkey', user=admin, method='POST')
        self.assertStatusOk(resp)
        self.assertIn(PluginSettings.HUB_PUB_KEY, resp.json)
        self.assertIn(PluginSettings.HUB_PRIV_KEY, resp.json)

        pubkey = resp.json[PluginSettings.HUB_PUB_KEY]

        resp = self.request(path='/ythub', method='GET')
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['url'], 'https://tmpnb.null')
        self.assertEqual(resp.json['pubkey'], pubkey)

        resp = self.request('/system/setting', user=admin, method='PUT',
                            params={'key': PluginSettings.REDIRECT_URL,
                                    'value': 'https://blah.null'})
        self.assertStatusOk(resp)
        resp = self.request(path='/ythub', method='GET')
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['url'], 'https://blah.null')

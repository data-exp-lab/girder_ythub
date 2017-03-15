from tests import base
from girder.constants import SettingKey


def setUpModule():
    base.enabledPlugins.append('ythub')
    base.startServer()


def tearDownModule():
    base.stopServer()


class YtHubTestCase(base.TestCase):

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

    def testHubRoutes(self):
        from girder.plugins.ythub.constants import PluginSettings
        self.model('setting').set(
            PluginSettings.TMPNB_URL, 'https://tmpnb.null')
        adminDef = {
            'email': 'root@dev.null',
            'login': 'admin',
            'firstName': 'Root',
            'lastName': 'van Klompf',
            'password': 'secret'
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

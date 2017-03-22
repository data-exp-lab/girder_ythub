
import httmock
import json
from tests import base
from .tests_helpers import \
    GOOD_REPO, GOOD_COMMIT, \
    mockOtherRequest, mockCommitRequest, mockReposRequest


def setUpModule():
    base.enabledPlugins.append('wholetale')
    base.startServer()


def tearDownModule():
    base.stopServer()


class TaleTestCase(base.TestCase):

    def setUp(self):
        super(TaleTestCase, self).setUp()
        global PluginSettings
        from girder.plugins.wholetale.constants import PluginSettings
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
        self.admin, self.user = [self.model('user').createUser(**user)
                                 for user in users]
        with httmock.HTTMock(mockReposRequest, mockCommitRequest,
                             mockOtherRequest):
            self.recipe = self.model('recipe', 'wholetale').createRecipe(
                GOOD_COMMIT, 'https://github.com/' + GOOD_REPO,
                creator=self.user, public=True)
        self.image = self.model('image', 'wholetale').createImage(
            self.recipe, GOOD_REPO, name="my name", creator=self.user,
            public=True)

        # Grab the default user folders
        resp = self.request(
            path='/folder', method='GET', user=self.user, params={
                'parentType': 'user',
                'parentId': self.user['_id'],
                'sort': 'name',
                'sortdir': 1
            })
        self.userPrivateFolder = resp.json[0]
        self.userPublicFolder = resp.json[1]

        self.tale_one = self.model('tale', 'wholetale').createTale(
            self.image, self.userPrivateFolder, creator=self.user,
            name='tale one', public=True, config={'memLimit': '2g'})
        self.tale_two = self.model('tale', 'wholetale').createTale(
            self.image, self.userPublicFolder, creator=self.user,
            name='tale one', public=True, config={'memLimit': '1g'})

    @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                      path='^/$', method='POST')
    def mockTmpnbHubPost(self, url, request):
        try:
            params = json.loads(request.body.decode('utf8'))
            self.assertIn(
                params['taleId'], (str(self.tale_one['_id']),
                                   str(self.tale_two['_id'])))
        except (KeyError, AssertionError) as e:
            return json.dumps({
                'status_code': 401,
                'content': json.dumps({'error': repr(e)})
            })

        return json.dumps({
            'mountPoint': '/var/lib/blah',
            'volumeName': '%s_%s' % (params['taleId'], str(self.user['_id'])),
            'containerId': '123456',
            'containerPath': '/user/blah',
            'host': '172.168.1.16'
        })

    def testInstanceFlow(self):
        # Grab the default user folders

        with httmock.HTTMock(self.mockTmpnbHubPost, mockOtherRequest):
            resp = self.request(
                path='/instance', method='POST', user=self.user,
                params={'taleId': str(self.tale_one['_id']),
                        'name': 'tale one'}
            )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['url'], '/user/blah')
        self.assertEqual(resp.json['name'], 'tale one')
        self.assertEqual(resp.json['containerInfo']['volumeName'],
                         '%s_%s' % (str(self.tale_one['_id']),
                                    str(self.user['_id'])))
        instance_one = resp.json

        with httmock.HTTMock(self.mockTmpnbHubPost, mockOtherRequest):
            resp = self.request(
                path='/instance', method='POST', user=self.user,
                params={'taleId': str(self.tale_two['_id'])},
            )
            self.assertStatusOk(resp)
            instance_two = resp.json

            resp = self.request(
                path='/instance', method='POST', user=self.admin,
                params={'taleId': str(self.tale_one['_id'])},
            )
            self.assertStatusOk(resp)
            instance_three = resp.json

            # Make sure that instance is a singleton
            resp = self.request(
                path='/instance', method='POST', user=self.admin,
                params={'taleId': str(self.tale_one['_id'])},
            )
            self.assertStatusOk(resp)
            self.assertEqual(resp.json['_id'], instance_three['_id'])

        resp = self.request(
            path='/instance', method='GET', user=self.user,
            params={}
        )
        self.assertStatusOk(resp)
        self.assertEqual(set([_['_id'] for _ in resp.json]),
                         {instance_one['_id'], instance_two['_id']})

        resp = self.request(
            path='/instance', method='GET', user=self.admin,
            params={'taleId': str(self.tale_one['_id'])}
        )
        self.assertStatusOk(resp)
        self.assertEqual(set([_['_id'] for _ in resp.json]),
                         {instance_one['_id'], instance_three['_id']})

        resp = self.request(
            path='/instance', method='GET', user=self.admin,
            params={'taleId': str(self.tale_one['_id']),
                    'userId': str(self.admin['_id'])}
        )
        self.assertStatusOk(resp)
        self.assertEqual(set([_['_id'] for _ in resp.json]),
                         {instance_three['_id']})

        @httmock.urlmatch(scheme='https', netloc='^tmpnb.null$',
                          path='^/$', method='DELETE')
        def mockTmpnbHubDelete(url, request):
            try:
                params = json.loads(request.body.decode('utf8'))
                self.assertEqual(
                    params['instanceId'], str(instance_two['_id']))
                self.assertEqual(request.headers['docker-host'],
                                 instance_two['containerInfo']['host'])
                self.assertEqual(request.headers['content-type'],
                                 'application/json')
            except (KeyError, AssertionError) as e:
                return json.dumps({
                    'status_code': 401,
                    'content': json.dumps({'error': repr(e)})
                })
            return httmock.response(
                200, None, None, None, 5, request)

        with httmock.HTTMock(mockTmpnbHubDelete, mockOtherRequest):
            resp = self.request(
                path='/instance/{_id}'.format(**instance_two), method='DELETE',
                user=self.user)
            self.assertStatusOk(resp)

        resp = self.request(
            path='/instance/{_id}'.format(**instance_two), method='GET',
            user=self.user)
        self.assertStatus(resp, 400)

        resp = self.request(
            path='/instance/{_id}'.format(**instance_one), method='GET',
            user=self.user)
        self.assertStatusOk(resp)
        for key in instance_one.keys():
            if key in ('access', 'updated', 'created', 'lastActivity'):
                continue
            self.assertEqual(resp.json[key], instance_one[key])

    def tearDown(self):
        self.model('user').remove(self.user)
        self.model('user').remove(self.admin)
        self.model('recipe', 'wholetale').remove(self.recipe)
        self.model('image', 'wholetale').remove(self.image)
        self.model('tale', 'wholetale').remove(self.tale_one)
        self.model('tale', 'wholetale').remove(self.tale_two)
        super(TaleTestCase, self).tearDown()

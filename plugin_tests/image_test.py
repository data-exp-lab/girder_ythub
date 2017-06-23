
import httmock
import json
from tests import base
from .tests_helpers import \
    GOOD_REPO, GOOD_COMMIT, GOOD_CHILD, \
    mockOtherRequest, mockCommitRequest, mockReposRequest


def setUpModule():
    base.enabledPlugins.append('wholetale')
    base.startServer()


def tearDownModule():
    base.stopServer()


class ImageTestCase(base.TestCase):

    def setUp(self):
        super(ImageTestCase, self).setUp()
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
            self.new_recipe = self.model('recipe', 'wholetale').createRecipe(
                GOOD_CHILD, 'https://github.com/' + GOOD_REPO,
                parent=self.recipe, creator=self.user, public=True)

    def testImageFlow(self):
        from girder.plugins.wholetale.constants import ImageStatus
        # test search modes
        resp = self.request(
            path='/image', method='POST', user=self.user,
            params={
                'fullName': GOOD_REPO, 'recipeId': str(self.recipe['_id']),
                'public': True}
        )
        self.assertStatusOk(resp)
        image = resp.json
        self.assertEqual(image['status'], ImageStatus.UNAVAILABLE)

        return  # This needs to be migrated to Job interface
        resp = self.request(
            path='/image/{_id}/build'.format(**image), method='PUT',
            user=self.admin)
        self.assertStatusOk(resp)
        self.assertEqual(image['_id'], resp.json['_id'])
        self.assertEqual(resp.json['status'], ImageStatus.BUILDING)

        resp = self.request(
            path='/image/{_id}/check'.format(**image), method='PUT',
            user=self.admin)
        self.assertStatusOk(resp)
        self.assertEqual(image['_id'], resp.json['_id'])
        self.assertEqual(resp.json['status'], ImageStatus.AVAILABLE)
        self.assertEqual(resp.json['digest'], 'set me')

        resp = self.request(
            path='/image/{_id}'.format(**image), method='PUT',
            user=self.user, params={
                'name': 'new name',
                'description': 'new description',
                'tags': json.dumps(['latest', 'foo']),
                'icon': 'http://lorempixel.com/200/200/cats/'
            }
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['name'], 'new name')
        image = resp.json

        resp = self.request(
            path='/image/{_id}/copy'.format(**image), method='POST',
            user=self.user, params={'recipeId': str(self.new_recipe['_id'])})
        self.assertStatusOk(resp)
        new_image = resp.json
        self.assertEqual(new_image['parentId'], image['_id'])

        resp = self.request(
            path='/image',  method='GET', user=self.user)
        self.assertStatusOk(resp)
        self.assertEqual(set([_['_id'] for _ in resp.json]),
                         {new_image['_id'], image['_id']})

        resp = self.request(
            path='/image/{_id}'.format(**new_image), method='GET',
            user=self.user)
        self.assertStatusOk(resp)
        for key in new_image.keys():
            if key in ('access', 'updated', 'created'):
                continue
            self.assertEqual(resp.json[key], new_image[key])

        resp = self.request(
            path='/image/{_id}'.format(**new_image), method='DELETE',
            user=self.admin)
        self.assertStatusOk(resp)

        resp = self.request(
            path='/image/{_id}'.format(**new_image), method='GET',
            user=self.user)
        self.assertStatus(resp, 400)

    def tearDown(self):
        self.model('user').remove(self.user)
        self.model('user').remove(self.admin)
        self.model('recipe', 'wholetale').remove(self.recipe)
        super(ImageTestCase, self).tearDown()

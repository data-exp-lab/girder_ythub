#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six
from tests import base


def setUpModule():
    base.enabledPlugins.append('wholetale')
    base.startServer()


def tearDownModule():
    base.stopServer()


class AssetFolderTestCase(base.TestCase):

    def testConfigValidators(self):
        from girder.plugins.wholetale.constants import PluginSettings
        adminDef = {
            'email': 'root0@dev.null',
            'login': 'admin0',
            'firstName': 'Root0',
            'lastName': 'van Klompf0',
            'password': 'secret0',
            'admin': True
        }
        user = self.model('user').createUser(**adminDef)

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

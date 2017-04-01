#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, getApiUrl
from girder.constants import AccessType

from girder.plugins.ythub.constants import PluginSettings


class ytHub(Resource):

    def __init__(self):
        super(ytHub, self).__init__()
        self.resourceName = 'ythub'

        self.route('GET', (), self.get_ythub_url)
        self.route('GET', (':id', 'examples'), self.generateExamples)
        self.route('POST', ('genkey',), self.generateRSAKey)

    @access.admin
    @autoDescribeRoute(
        Description('Generate ythub\'s RSA key')
    )
    def generateRSAKey(self, params):
        rsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        pubkey_pem = rsa_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf8')
        privkey_pem = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf8')
        self.model('setting').set(PluginSettings.HUB_PUB_KEY, pubkey_pem)
        self.model('setting').set(PluginSettings.HUB_PRIV_KEY, privkey_pem)
        return {PluginSettings.HUB_PUB_KEY: pubkey_pem,
                PluginSettings.HUB_PRIV_KEY: privkey_pem}

    @access.public
    @autoDescribeRoute(
        Description('Return url for tmpnb hub.')
    )
    def get_ythub_url(self, params):
        setting = self.model('setting')
        url = setting.get(PluginSettings.REDIRECT_URL)
        if not url:
            url = setting.get(PluginSettings.TMPNB_URL)
        return {'url': url,
                'pubkey': setting.get(PluginSettings.HUB_PUB_KEY)}

    @access.public
    @autoDescribeRoute(
        Description('Generate example data page.')
        .modelParam('id', model='folder', level=AccessType.READ)
    )
    def generateExamples(self, folder, params):
        def get_code(resource):
            try:
                return resource["meta"]["code"]
            except KeyError:
                return "unknown"

        def sizeof_fmt(num, suffix='B'):
            for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
                if abs(num) < 1024.0:
                    return "%3.1f%s%s" % (num, unit, suffix)
                num /= 1024.0
            return "%.1f%s%s" % (num, 'Yi', suffix)

        def download_path(_id, resource):
            return "{}/{}/{}/download".format(getApiUrl(), resource, _id)

        result = {}
        user = self.getCurrentUser()
        frontends = list(
            self.model('folder').childFolders(parentType='folder',
                                              parent=folder, user=user))
        for frontend in frontends:
            ds = list(
                self.model('folder').childFolders(parentType='folder',
                                                  parent=frontend, user=user))

            examples = [dict(code=get_code(_), description=_["description"],
                             filename=_["name"], size=sizeof_fmt(_["size"]),
                             url=download_path(_["_id"], "folder"))
                        for _ in ds]
            ds = list(self.model('folder').childItems(folder=frontend))
            examples += [dict(code=get_code(_), description=_["description"],
                              filename=_["name"], size=sizeof_fmt(_["size"]),
                              url=download_path(_["_id"], "item"))
                         for _ in ds]
            result[frontend["name"]] = examples

        return result

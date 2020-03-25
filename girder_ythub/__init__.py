#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import six

from girder import events
from girder.models.assetstore import Assetstore
from girder.models.collection import Collection
from girder.models.folder import Folder
from girder.models.item import Item
from girder.models.model_base import ValidationException
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import boundHandler, loadmodel
from girder.constants import AccessType, TokenScope
from girder.plugin import getPlugin, GirderPlugin
from girder.utility.model_importer import ModelImporter
from girder.utility import assetstore_utilities, setting_utilities

from .constants import PluginSettings
from .rest.frontend import Frontend
from .rest.notebook import Notebook
from .rest.raft import Raft
from .rest.ythub import ytHub

from .models.frontend import Frontend as frontendModel
from .models.notebook import Notebook as notebookModel


@setting_utilities.validator(PluginSettings.HUB_PRIV_KEY)
def validateHubPrivKey(doc):
    if not doc['value']:
        raise ValidationException(
            'PRIV_KEY must not be empty.', 'value')
    key = doc['value']
    if isinstance(key, six.string_types):
        key = key.encode('utf-8')
    try:
        serialization.load_pem_private_key(
            key, password=None, backend=default_backend()
        )
    except ValueError:
        raise ValidationException(
            "PRIV_KEY's data structure could not be decoded.")
    except TypeError:
        raise ValidationException(
            "PRIV_KEY is password encrypted, yet no password provided.")
    except UnsupportedAlgorithm:
        raise ValidationException(
            "PRIV_KEY's type is not supported.")


@setting_utilities.validator(PluginSettings.HUB_PUB_KEY)
def validateHubPubKey(doc):
    if not doc['value']:
        raise ValidationException(
            'PUB_KEY must not be empty.', 'value')
    key = doc['value']
    if isinstance(key, six.string_types):
        key = key.encode('utf-8')
    try:
        serialization.load_pem_public_key(
            key, backend=default_backend()
        )
    except ValueError:
        raise ValidationException(
            "PUB_KEY's data structure could not be decoded.")
    except UnsupportedAlgorithm:
        raise ValidationException(
            "PUB_KEY's type is not supported.")


@setting_utilities.validator(PluginSettings.TMPNB_URL)
def validateTmpNbUrl(doc):
    if not doc['value']:
        raise ValidationException(
            'TmpNB URL must not be empty.', 'value')


@setting_utilities.validator(PluginSettings.REDIRECT_URL)
def validateTmpNbRedirectUrl(doc):
    if not doc['value']:
        return ''


@setting_utilities.validator(PluginSettings.CULLING_PERIOD)
def validateCullingPeriod(doc):
    if not doc['value']:
        raise ValidationException(
            'Culling period must not be empty.', 'value')
    try:
        float(doc['value'])
    except ValueError:
        raise ValidationException(
            'Culling period must float.', 'value')


@setting_utilities.validator(PluginSettings.CULLING_FREQUENCY)
def validateCullingFrequency(doc):
    if not doc['value']:
        raise ValidationException(
            'Culling frequency must not be empty.', 'value')
    try:
        float(doc['value'])
    except ValueError:
        raise ValidationException(
            'Culling frequency must float.', 'value')


@access.public(scope=TokenScope.DATA_READ)
@loadmodel(model='folder', level=AccessType.READ)
@describeRoute(
    Description('List the content of a folder.')
    .param('id', 'The ID of the folder.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the folder.', 403)
)
@boundHandler()
def listFolder(self, folder, params):
    user = self.getCurrentUser()
    folders = list(
        Folder().childFolders(parentType='folder', parent=folder, user=user))

    files = []
    for item in Folder().childItems(folder=folder):
        childFiles = list(Item().childFiles(item))
        if len(childFiles) == 1:
            fileitem = childFiles[0]
            if 'imported' not in fileitem and \
                    fileitem.get('assetstoreId') is not None:
                try:
                    store = \
                        Assetstore().load(fileitem['assetstoreId'])
                    adapter = assetstore_utilities.getAssetstoreAdapter(store)
                    fileitem["path"] = adapter.fullPath(fileitem)
                except ValidationException:
                    pass
            files.append(fileitem)
        else:
            folders.append(item)
    return {'folders': folders, 'files': files}


@access.public(scope=TokenScope.DATA_OWN)
@loadmodel(model='item', level=AccessType.ADMIN)
@describeRoute(
    Description('Perform system check for a given item.')
    .param('id', 'The ID of the item.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the item.', 403)
)
@boundHandler()
def checkItem(self, item, params):
    Item().updateSize(item)


@access.public(scope=TokenScope.DATA_OWN)
@loadmodel(model='folder', level=AccessType.ADMIN)
@describeRoute(
    Description('Perform system check for a given folder.')
    .param('id', 'The ID of the folder.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the folder.', 403)
)
@boundHandler()
def checkFolder(self, folder, params):
    Folder().updateSize(folder)


@access.public(scope=TokenScope.DATA_OWN)
@loadmodel(model='collection', level=AccessType.ADMIN)
@describeRoute(
    Description('Perform system check for a given collection.')
    .param('id', 'The ID of the collection.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the collection.', 403)
)
@boundHandler()
def checkCollection(self, collection, params):
    Collection().updateSize(collection)


@access.public(scope=TokenScope.DATA_READ)
@loadmodel(model='item', level=AccessType.READ)
@describeRoute(
    Description('List the content of an item.')
    .param('id', 'The ID of the folder.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the folder.', 403)
)
@boundHandler()
def listItem(self, item, params):
    files = []
    for fileitem in Item().childFiles(item):
        if 'imported' not in fileitem and \
                fileitem.get('assetstoreId') is not None:
            try:
                store = \
                    Assetstore().load(fileitem['assetstoreId'])
                adapter = assetstore_utilities.getAssetstoreAdapter(store)
                fileitem["path"] = adapter.fullPath(fileitem)
            except ValidationException:
                pass
        files.append(fileitem)
    return {'folders': [], 'files': files}


@access.public(scope=TokenScope.DATA_READ)
@loadmodel(model='folder', level=AccessType.READ)
@describeRoute(
    Description('Get the path to the root of the folder\'s hierarchy.')
    .param('id', 'The ID of the folder.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the item.', 403)
)
@boundHandler()
def folderRootpath(self, folder, params):
    return Folder().parentsToRoot(
        folder, user=self.getCurrentUser())


def addDefaultFolders(event):
    user = event.info
    notebookFolder = ModelImporter.model('folder').createFolder(
        user, 'Notebooks', parentType='user', public=False, creator=user)
    ModelImporter.model('folder').setUserAccess(
        notebookFolder, user, AccessType.ADMIN, save=True)


class ytHubPlugin(GirderPlugin):
    DISPLAY_NAME = "ytHub on Girder"
    CLIENT_SOURCE_PATH = "web_client"

    def load(self, info):
        ModelImporter.registerModel("notebook", notebookModel, plugin="ythub")
        ModelImporter.registerModel("frontend", frontendModel, plugin="ythub")
        info['apiRoot'].ythub = ytHub()
        info['apiRoot'].notebook = Notebook()
        info['apiRoot'].frontend = Frontend()
        info['apiRoot'].raft = Raft()
        info['apiRoot'].folder.route('GET', (':id', 'listing'), listFolder)
        info['apiRoot'].item.route('GET', (':id', 'listing'), listItem)
        info['apiRoot'].item.route('PUT', (':id', 'check'), checkItem)
        info['apiRoot'].folder.route('GET', (':id', 'rootpath'), folderRootpath)
        info['apiRoot'].folder.route('PUT', (':id', 'check'), checkFolder)
        info['apiRoot'].collection.route('PUT', (':id', 'check'), checkCollection)

        Item().ensureIndex(['meta.isRaft', {'sparse': True}])

        events.bind('model.user.save.created', 'ythub', addDefaultFolders)

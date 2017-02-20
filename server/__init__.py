#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import six

from girder import events  # , logger
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import \
    boundHandler, loadmodel, getCurrentUser, RestException
from girder.constants import AccessType, TokenScope
from girder.models.model_base import ValidationException
from girder.utility import assetstore_utilities, setting_utilities
from girder.utility.model_importer import ModelImporter

from .constants import PluginSettings
from .rest.recipe import Recipe
from .rest.image import Image
from .rest.repository import Repository
from .rest.search import DatasetSearchEngine
from .rest.tale import Tale
from .rest.notebook import Notebook
from .rest.ythub import ytHub


_last_culling = datetime.datetime.utcnow()


@setting_utilities.validator(PluginSettings.HUB_PRIV_KEY)
def validateHubPrivKey(doc):
    if not doc['value']:
        raise ValidationException(
            'PRIV_KEY must not be empty.', 'value')
    try:
        serialization.load_pem_private_key(
            doc['value'].encode('utf8'),
            password=None,
            backend=default_backend()
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
    try:
        serialization.load_pem_public_key(
            doc['value'].encode('utf8'),
            backend=default_backend()
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


@setting_utilities.validator(PluginSettings.CULLING_PERIOD)
def validateCullingPeriod(doc):
    try:
        float(doc['value'])
    except KeyError:
        raise ValidationException(
            'Culling period must not be empty.', 'value')
    except ValueError:
        raise ValidationException(
            'Culling period must float.', 'value')


def saveImportPathToMeta(event):
    resourceModel = ModelImporter.model(event.info['type'])
    resource = resourceModel.load(event.info['id'], user=getCurrentUser())
    resourceModel.setMetadata(resource,
                              {"phys_path": event.info['importPath']})


@access.public(scope=TokenScope.DATA_READ)
@loadmodel(model='folder', level=AccessType.READ)
@describeRoute(
    Description('Get physical paths for files in folder.')
    .param('id', 'The ID of the folder.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the folder.', 403)
)
@boundHandler()
def getFolderFilesMapping(self, folder, params):
    user = self.getCurrentUser()
    result = {}
    for (path, item) in self.model('folder').fileList(
            folder, user=user, subpath=False, data=False):
        assetstore = self.model('assetstore').load(item['assetstoreId'])
        adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        result[path] = adapter.fullPath(item)
    return result


@access.public(scope=TokenScope.DATA_READ)
@loadmodel(model='item', level=AccessType.READ)
@describeRoute(
    Description('Get physical paths for files in item.')
    .param('id', 'The ID of the folder.', paramType='path')
    .errorResponse('ID was invalid.')
    .errorResponse('Read access was denied for the folder.', 403)
)
@boundHandler()
def getItemFilesMapping(self, item, params):
    user = self.getCurrentUser()
    result = {}
    for (path, fileitem) in self.model('item').fileList(
            item, user=user, subpath=False, data=False):
        assetstore = self.model('assetstore').load(fileitem['assetstoreId'])
        adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        result[path] = adapter.fullPath(fileitem)
    return result


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
        self.model('folder').childFolders(parentType='folder',
                                          parent=folder, user=user))

    files = []
    for item in self.model('folder').childItems(folder=folder):
        childFiles = list(self.model('item').childFiles(item))
        if len(childFiles) == 1:
            fileitem = childFiles[0]
            if 'imported' not in fileitem and \
                    fileitem.get('assetstoreId') is not None:
                try:
                    store = \
                        self.model('assetstore').load(fileitem['assetstoreId'])
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
    self.model('item').updateSize(item)


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
    self.model('folder').updateSize(folder)


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
    self.model('collection').updateSize(collection)


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
    for fileitem in self.model('item').childFiles(item):
        if 'imported' not in fileitem and \
                fileitem.get('assetstoreId') is not None:
            store = \
                self.model('assetstore').load(fileitem['assetstoreId'])
            adapter = assetstore_utilities.getAssetstoreAdapter(store)
            fileitem["path"] = adapter.fullPath(fileitem)
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
    return self.model('folder').parentsToRoot(
        folder, user=self.getCurrentUser())


def cullNotebooks(event):
    global _last_culling
    culling_freq = datetime.timedelta(minutes=1)
    if datetime.datetime.utcnow() - culling_freq > _last_culling:
        ModelImporter.model('notebook', 'ythub').cullNotebooks()
        _last_culling = datetime.datetime.utcnow()


@access.public(scope=TokenScope.USER_INFO_READ)
@describeRoute(
    Description('Update the user settings.')
    .errorResponse('Read access was denied.', 403)
)
@boundHandler()
def getUserMetadata(self, params):
    user = self.getCurrentUser()
    if user is None:
        return {}
    return user.get('meta', {})


@access.public(scope=TokenScope.USER_INFO_READ)
@describeRoute(
    Description('Get the user settings.')
    .param('body', 'A JSON object containing the metadata keys to add',
           paramType='body')
    .errorResponse('Write access was denied.', 403)
)
@boundHandler()
def setUserMetadata(self, params):
    user = self.getCurrentUser()
    if user is None:
        return {}

    metadata = self.getBodyJson()

    # Make sure we let user know if we can't accept a metadata key
    for k in metadata:
        if not len(k):
            raise RestException('Key names must be at least one character long.')
        if '.' in k or k[0] == '$':
            raise RestException('The key name %s must not contain a period '
                                'or begin with a dollar sign.' % k)

    if 'meta' not in user:
        user['meta'] = {}

    # Add new metadata to existing metadata
    user['meta'].update(six.viewitems(metadata))

    # Remove metadata fields that were set to null (use items in py3)
    toDelete = [k for k, v in six.viewitems(user['meta']) if v is None]
    for key in toDelete:
        del user['meta'][key]

    # Validate and save the user
    return self.model('user').save(user)


def load(info):
    events.bind('filesystem_assetstore_imported', 'ythub',
                saveImportPathToMeta)
    events.bind('heartbeat', 'ythub', cullNotebooks)
    info['apiRoot'].ythub = ytHub()
    info['apiRoot'].notebook = Notebook()
    info['apiRoot'].tale = Tale()
    info['apiRoot'].recipe = Recipe()
    info['apiRoot'].image = Image()
    info['apiRoot'].repository = Repository()
    info['apiRoot'].search = DatasetSearchEngine()
    info['apiRoot'].folder.route('GET', (':id', 'contents'),
                                 getFolderFilesMapping)
    info['apiRoot'].item.route('GET', (':id', 'contents'), getItemFilesMapping)
    info['apiRoot'].folder.route('GET', (':id', 'listing'), listFolder)
    info['apiRoot'].item.route('GET', (':id', 'listing'), listItem)
    info['apiRoot'].item.route('PUT', (':id', 'check'), checkItem)
    info['apiRoot'].folder.route('GET', (':id', 'rootpath'), folderRootpath)
    info['apiRoot'].folder.route('PUT', (':id', 'check'), checkFolder)
    info['apiRoot'].collection.route('PUT', (':id', 'check'), checkCollection)

    info['apiRoot'].user.route('PUT', ('settings',), setUserMetadata)
    info['apiRoot'].user.route('GET', ('settings',), getUserMetadata)

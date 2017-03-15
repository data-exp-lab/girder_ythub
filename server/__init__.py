#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from girder import events, logger
from girder.models.model_base import ValidationException
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import boundHandler, loadmodel
from girder.constants import AccessType, TokenScope

from girder.utility.model_importer import ModelImporter
from girder.utility import assetstore_utilities, config, setting_utilities
from girder.api.rest import getCurrentUser

from .constants import PluginSettings
from .rest.frontend import Frontend
from .rest.notebook import Notebook
from .rest.ythub import ytHub


@setting_utilities.validator(PluginSettings.HUB_PRIV_KEY)
def validateHubPrivKey(doc):
    if not doc['value']:
        raise ValidationException(
            'PRIV_KEY must not be empty.', 'value')
    try:
        key = doc['value'].encode('utf8')
    except AttributeError:
        key = doc['value']
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
    try:
        key = doc['value'].encode('utf8')
    except AttributeError:
        key = doc['value']
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


@setting_utilities.validator(PluginSettings.CULLING_FREQUENCY)
def validateCullingFrequency(doc):
    try:
        float(doc['value'])
    except KeyError:
        raise ValidationException(
            'Culling frequency must not be empty.', 'value')
    except ValueError:
        raise ValidationException(
            'Culling frequency must float.', 'value')


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


def addDefaultFolders(event):
    user = event.info
    notebookFolder = ModelImporter.model('folder').createFolder(
        user, 'Notebooks', parentType='user', public=False, creator=user)
    ModelImporter.model('folder').setUserAccess(
        notebookFolder, user, AccessType.ADMIN, save=True)


def load(info):
    notebook = Notebook()
    info['apiRoot'].ythub = ytHub()
    info['apiRoot'].notebook = notebook
    info['apiRoot'].frontend = Frontend()
    info['apiRoot'].folder.route('GET', (':id', 'contents'),
                                 getFolderFilesMapping)
    info['apiRoot'].item.route('GET', (':id', 'contents'), getItemFilesMapping)
    info['apiRoot'].folder.route('GET', (':id', 'listing'), listFolder)
    info['apiRoot'].item.route('GET', (':id', 'listing'), listItem)
    info['apiRoot'].item.route('PUT', (':id', 'check'), checkItem)
    info['apiRoot'].folder.route('GET', (':id', 'rootpath'), folderRootpath)
    info['apiRoot'].folder.route('PUT', (':id', 'check'), checkFolder)
    info['apiRoot'].collection.route('PUT', (':id', 'check'), checkCollection)

    curConfig = config.getConfig()
    if curConfig['server']['mode'] == 'testing':
        cull_period = 1
    else:
        cull_period = int(curConfig['server'].get('heartbeat', -1))

    if cull_period > 0:

        def _heartbeat():
            events.trigger('heartbeat')

        logger.info('Starting Heartbeat every %i s' % cull_period)
        heartbeat = cherrypy.process.plugins.Monitor(
            cherrypy.engine, _heartbeat, frequency=cull_period,
            name="Heartbeat")
        heartbeat.subscribe()
        events.bind('heartbeat', 'ythub', notebook.cullNotebooks)

    events.bind('filesystem_assetstore_imported', 'ythub',
                saveImportPathToMeta)
    events.bind('model.user.save.created', 'ythub', addDefaultFolders)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from girder import events  # , logger
from girder.models.model_base import ValidationException
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import boundHandler, Resource, filtermodel, loadmodel
from girder.constants import AccessType, SortDir, TokenScope
from .constants import PluginSettings

from girder.utility.model_importer import ModelImporter
from girder.utility import assetstore_utilities, setting_utilities
from girder.api.rest import getCurrentUser, getApiUrl


_last_culling = datetime.datetime.utcnow()


class Job(Resource):

    def __init__(self):
        super(Job, self).__init__()


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


class ytHub(Resource):

    def __init__(self):
        super(ytHub, self).__init__()
        self.resourceName = 'ythub'

        self.route('GET', (), self.get_ythub_url)
        self.route('GET', (':id', 'examples'), self.generateExamples)

    @access.public
    @describeRoute(
        Description('Return url for tmpnb hub.')
    )
    def get_ythub_url(self, params):
        return {'url': self.model('setting').get(PluginSettings.TMPNB_URL)}

    @access.public
    @loadmodel(model='folder', level=AccessType.READ)
    @describeRoute(
        Description('Generate example data page.')
        .param('id', 'The folder ID which holds example data.',
               paramType='path')
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


class Notebook(Resource):

    def __init__(self):
        super(Notebook, self).__init__()
        self.resourceName = 'notebook'

        self.route('GET', (), self.listNotebooks)
        self.route('GET', (':id',), self.getNotebook)
        self.route('POST', (':id',), self.createNotebook)
        self.route('DELETE', (':id',), self.deleteNotebook)

    @access.user
    @filtermodel(model='notebook', plugin='ythub')
    @describeRoute(
        Description('List notebooks for a given user.')
        .param('userId', 'The ID of the user whose notebooks will be listed. '
               'If not passed or empty, will use the currently logged in user.'
               ' If set to "None", will list all notebooks that do not have '
               'an owning user.', required=False)
        .param('folderId', 'The folder ID which notebooks will be listed. ',
               required=False)
        .pagingParams(defaultSort='created', defaultSortDir=SortDir.DESCENDING)
    )
    def listNotebooks(self, params):
        limit, offset, sort = self.getPagingParameters(
            params, 'created', SortDir.DESCENDING)
        currentUser = self.getCurrentUser()
        userId = params.get('userId')
        folderId = params.get('folderId')
        if not userId or userId.lower() == 'none':
            user = None
        else:
            user = self.model('user').load(
                userId, user=currentUser, level=AccessType.READ)

        if not folderId or folderId.lower() == 'none':
            folder = None
        else:
            folder = self.model('folder').load(
                params['folderId'], user=currentUser, level=AccessType.READ)

        return list(self.model('notebook', 'ythub').list(
            user=user, folder=folder, offset=offset, limit=limit,
            sort=sort, currentUser=currentUser))

    @access.user
    @loadmodel(model='notebook', plugin='ythub', level=AccessType.READ)
    @describeRoute(
        Description('Get a notebook by ID.')
        .param('id', 'The ID of the notebook.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the notebook.', 403)
    )
    @filtermodel(model='notebook', plugin='ythub')
    def getNotebook(self, notebook, params):
        return notebook

    @access.user
    @loadmodel(model='notebook', plugin='ythub', level=AccessType.WRITE)
    @describeRoute(
        Description('Delete an existing notebook.')
        .param('id', 'The ID of the notebook.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Write access was denied for the notebook.', 403)
    )
    def deleteNotebook(self, notebook, params):
        self.model('notebook', 'ythub').deleteNotebook(
            notebook, self.getCurrentToken())

    @access.user
    @loadmodel(model='folder', level=AccessType.READ)
    @filtermodel(model='notebook', plugin='ythub')
    @describeRoute(
        Description('Create new notebook for a current user and folder.')
        .notes('The output image is placed in the same parent folder as the '
               'input image.')
        .param('id', 'The ID of the item containing the input image.',
               paramType='path')
    )
    def createNotebook(self, folder, params):
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        # folder = self.model('folder').load(item['folderId'], force=True)
        notebookModel = self.model('notebook', 'ythub')

        notebook = notebookModel.createNotebook(folder, user, token)

        return notebookModel.save(notebook)


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
            if 'imported' not in fileitem:
                store = \
                    self.model('assetstore').load(fileitem['assetstoreId'])
                adapter = assetstore_utilities.getAssetstoreAdapter(store)
                fileitem["path"] = adapter.fullPath(fileitem)
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
        if 'imported' not in fileitem:
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


def load(info):
    events.bind('filesystem_assetstore_imported', 'ythub',
                saveImportPathToMeta)
    events.bind('heartbeat', 'ythub', cullNotebooks)
    info['apiRoot'].ythub = ytHub()
    info['apiRoot'].notebook = Notebook()
    info['apiRoot'].folder.route('GET', (':id', 'contents'),
                                 getFolderFilesMapping)
    info['apiRoot'].item.route('GET', (':id', 'contents'), getItemFilesMapping)
    info['apiRoot'].folder.route('GET', (':id', 'listing'), listFolder)
    info['apiRoot'].item.route('GET', (':id', 'listing'), listItem)
    info['apiRoot'].item.route('PUT', (':id', 'check'), checkItem)
    info['apiRoot'].folder.route('GET', (':id', 'rootpath'), folderRootpath)
    info['apiRoot'].folder.route('PUT', (':id', 'check'), checkFolder)

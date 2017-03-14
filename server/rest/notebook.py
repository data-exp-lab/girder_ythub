#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.docs import addModel
from girder.api.rest import Resource, loadmodel, filtermodel
from girder.constants import AccessType, SortDir


notebookModel = {
    'id': 'notebook',
    'type': 'object',
    'required': [
        '_accessLevel', '_id', '_modelType', 'containerId',
        'containerPath', 'created', 'folderId', 'frontendId',
        'lastActivity', 'mountPoint', 'status', 'userId',
        'when'
    ],
    'example': {
        '_accessLevel': 2,
        '_id': '587506670791d3000121b68d',
        '_modelType': 'notebook',
        'containerId': '7086458236c55f336f78bb0e3cbe7233df07499abb0f943f2',
        'containerPath': 'user/kvmKuSBUDydo',
        'created': '2017-01-10T16:05:56.296000+00:00',
        'folderId': '5873dc0faec030000144d232',
        'frontendId': '5873dcdbaec030000144d233',
        'lastActivity': '2017-01-10T16:05:56.296000+00:00',
        'mountPoint': '/var/lib/docker/volumes/5873dc0faec0300_root/_data',
        'status': 0,
        'userId': '586fe9414bd053000185b45d',
        'when': '2017-01-10T16:05:56.296000+00:00'
    },
    'properties': {
        '_accessLevel': {'type': 'integer', 'format': 'int32'},
        '_id': {'type': 'string'},
        '_modelType': {'type': 'string'},
        'containerId': {'type': 'string'},
        'containerPath': {'type': 'string'},
        'created': {'type': 'string', 'format': 'date'},
        'folderId': {'type': 'string'},
        'frontendId': {'type': 'string'},
        'lastActivity': {'type': 'string', 'format': 'date'},
        'mountPoint': {'type': 'string'},
        'status': {'type': 'integer', 'format': 'int32',
                   'allowEmptyValue': False,
                   'maximum': 1, 'minimum': 0},
        'userId': {'type': 'string'},
        'when': {'type': 'string', 'format': 'date'},
    }
}
addModel('notebook', notebookModel, resources='notebook')


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
        .responseClass('notebook', array=True)
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
        .responseClass('notebook')
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
        .param('id', 'The ID of the folder that will be mounted inside '
               'of the container.', paramType='path')
        .param('frontendId', 'The ID of the frontend that is going to be '
               'started.', required=False)
        .responseClass('notebook')
    )
    def createNotebook(self, folder, params):
        self.requireParams(('frontendId'), params)
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        # folder = self.model('folder').load(item['folderId'], force=True)
        notebookModel = self.model('notebook', 'ythub')
        frontend = self.model('frontend', 'ythub').load(params['frontendId'],
                                                        force=True)
        notebook = notebookModel.createNotebook(folder, user, token, frontend)

        return notebookModel.save(notebook)

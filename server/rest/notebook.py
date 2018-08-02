#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.docs import addModel
from girder.api.rest import Resource, filtermodel
from girder.constants import AccessType, SortDir


notebookModel = {
    'id': 'notebook',
    'type': 'object',
    'required': [
        '_id', 'folderId', 'frontendId', 'creator', 'serviceInfo',
    ],
    'example': {
        '_accessLevel': 2,
        '_id': '587506670791d3000121b68d',
        '_modelType': 'notebook',
        'created': '2017-01-10T16:05:56.296000+00:00',
        'folderId': '5873dc0faec030000144d232',
        'frontendId': '5873dcdbaec030000144d233',
        'status': 0,
        'userId': '586fe9414bd053000185b45d',
        'when': '2017-01-10T16:05:56.296000+00:00'
    },
    'properties': {
        '_id': {'type': 'string'},
        'created': {'type': 'string', 'format': 'date'},
        'creatorId': {'type': 'string'},
        'folderId': {'type': 'string'},
        'frontendId': {'type': 'string'},
        'lastActivity': {'type': 'string', 'format': 'date'},
        'status': {'type': 'integer', 'format': 'int32',
                   'allowEmptyValue': False,
                   'maximum': 1, 'minimum': 0},
    }
}
addModel('notebook', notebookModel, resources='notebook')


class Notebook(Resource):

    def __init__(self):
        super(Notebook, self).__init__()
        self.resourceName = 'notebook'

        self.route('GET', (), self.listNotebooks)
        self.route('POST', (), self.createNotebook)
        self.route('GET', (':id',), self.getNotebook)
        self.route('DELETE', (':id',), self.deleteNotebook)

        self.lastCulling = datetime.datetime.utcnow()

    @access.user
    @filtermodel(model='notebook', plugin='ythub')
    @autoDescribeRoute(
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
    def listNotebooks(self, userId, folderId, limit, offset, sort, params):
        currentUser = self.getCurrentUser()
        if not userId or userId.lower() == 'none':
            user = None
        else:
            user = self.model('user').load(
                userId, user=currentUser, level=AccessType.READ)

        if not folderId or folderId.lower() == 'none':
            folder = None
        else:
            folder = self.model('folder').load(
                folderId, user=currentUser, level=AccessType.READ)

        return list(self.model('notebook', 'ythub').list(
            user=user, folder=folder, offset=offset, limit=limit,
            sort=sort, currentUser=currentUser))

    @access.user
    @autoDescribeRoute(
        Description('Get a notebook by ID.')
        .modelParam('id', model='notebook', plugin='ythub',
                    level=AccessType.READ)
        .responseClass('notebook')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the notebook.', 403)
    )
    @filtermodel(model='notebook', plugin='ythub')
    def getNotebook(self, notebook, params):
        return notebook

    @access.user
    @autoDescribeRoute(
        Description('Delete an existing notebook.')
        .modelParam('id', model='notebook', plugin='ythub',
                    level=AccessType.WRITE)
        .errorResponse('ID was invalid.')
        .errorResponse('Write access was denied for the notebook.', 403)
    )
    def deleteNotebook(self, notebook, params):
        self.model('notebook', 'ythub').deleteNotebook(
            notebook, self.getCurrentToken())

    @access.user
    @filtermodel(model='notebook', plugin='ythub')
    @autoDescribeRoute(
        Description('Create new notebook for a current user and folder.')
        .param('folderId', 'The ID of the folder that will be mounted inside '
               'of the container.', required=True)
        .param('frontendId', 'The ID of the frontend that is going to be '
               'started.', required=True)
        .jsonParam('scripts', 'An array containing IDs of items that are '
                   'going to be downloaded.',
                   paramType='form', requireArray=True, required=False)
        .responseClass('notebook')
    )
    def createNotebook(self, folderId, frontendId, scripts, params):
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        notebookModel = self.model('notebook', 'ythub')
        frontend = self.model('frontend', 'ythub').load(
            frontendId, user=user, level=AccessType.READ)
        folder = self.model('folder').load(
            folderId, user=user, level=AccessType.READ)
        notebook = notebookModel.createNotebook(folder, user, token, frontend,
                                                scripts)

        return notebookModel.save(notebook)

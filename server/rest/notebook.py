#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, loadmodel, filtermodel
from girder.constants import AccessType, SortDir


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

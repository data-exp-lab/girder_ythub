#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder import events
from girder.models.model_base import ValidationException
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, filtermodel, loadmodel
from girder.constants import AccessType, SortDir
from .constants import PluginSettings


class Job(Resource):
    def __init__(self):
        super(Job, self).__init__()


def validateSettings(event):
    if event.info['key'] == PluginSettings.TMPNB_URL:
        if not event.info['value']:
            raise ValidationException(
                'TmpNB URL must not be empty.', 'value')
        event.preventDefault().stopPropagation()


class ytHub(Resource):
    def __init__(self):
        self.resourceName = 'ythub'

        self.route('GET', (), self.get_ythub_url)

    @access.public
    def get_ythub_url(self, params):
        settingModel = self.model('setting')
        return {'url': settingModel.get(PluginSettings.TMPNB_URL)}


class Notebook(Resource):
    def __init__(self):
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
        if not userId:
            user = currentUser
        elif userId.lower() == 'none':
            user = None
        else:
            user = self.model('user').load(
                params['userId'], user=currentUser, level=AccessType.READ)

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
        self.model('notebook', 'ythub').remove(notebook)

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
        # token = self.getCurrentToken()
        # folder = self.model('folder').load(item['folderId'], force=True)
        notebookModel = self.model('notebook', 'ythub')

        url = "FIXME"  # get from post

        notebook = notebookModel.createNotebook(folder, user, url)
        return notebookModel.save(notebook)


def load(info):
    events.bind('model.setting.validate', 'ythub', validateSettings)
    info['apiRoot'].ythub = ytHub()
    info['apiRoot'].notebook = Notebook()

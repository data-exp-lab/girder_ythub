#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, loadmodel, filtermodel
from girder.constants import AccessType, SortDir


class Frontend(Resource):

    def __init__(self):
        super(Frontend, self).__init__()
        self.resourceName = 'frontend'

        self.route('GET', (), self.listFrontends)
        self.route('GET', (':id',), self.getFrontend)
        self.route('PUT', (':id',), self.updateFrontend)
        self.route('POST', (), self.createFrontend)
        self.route('DELETE', (':id',), self.deleteFrontend)

    @access.public
    @filtermodel(model='frontend', plugin='ythub')
    @describeRoute(
        Description('List available frontends.')
        .pagingParams(defaultSort='imageName',
                      defaultSortDir=SortDir.DESCENDING)
    )
    def listFrontends(self, params):
        user = self.getCurrentUser()
        limit, offset, sort = self.getPagingParameters(
            params, 'imageName', SortDir.DESCENDING)
        return list(self.model('frontend', 'ythub').list(
            user=user, offset=offset, limit=limit, sort=sort))

    @access.public
    @filtermodel(model='frontend', plugin='ythub')
    @loadmodel(model='frontend', plugin='ythub', level=AccessType.READ)
    @describeRoute(
        Description('Get a frontend by ID.')
        .param('id', 'The ID of the frontend.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    def getFrontend(self, frontend, params):
        return frontend

    @access.admin
    @loadmodel(model='frontend', plugin='ythub', level=AccessType.ADMIN)
    @describeRoute(
        Description('Update an existing frontend.')
        .param('id', 'The ID of the frontend.', paramType='path')
        .param('imageName', 'A docker image name.', required=False)
        .param('command', 'The main command run inside the container.',
               required=False)
        .param('memLimit', 'Impose RAM limit for the running container.',
               required=False)
        .param('user', 'User that will be running session inside '
               'the container.', required=False)
        .param('port', 'Bind specified within-container port.',
               required=False)
        .param('description', 'Short info about the image content.',
               required=False)
        .param('cpuShares', 'Limit cpu usage.', required=False)
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the frontend.', 403)
    )
    def updateFrontend(self, frontend, params):
        for key in ('imageName', 'command', 'memLimit', 'user', 'port',
                    'cpuShares', 'description'):
            if key not in frontend:
                frontend[key] = None
            frontend[key] = params.get(key, frontend[key])
            if frontend[key] is not None:
                frontend[key] = frontend[key].strip()
        return self.model('frontend', 'ythub').updateFrontend(frontend)

    @access.admin
    @loadmodel(model='frontend', plugin='ythub', level=AccessType.ADMIN)
    @describeRoute(
        Description('Delete an existing frontend.')
        .param('id', 'The ID of the frontend.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the frontend.', 403)
    )
    def deleteFrontend(self, frontend, params):
        self.model('frontend', 'ythub').remove(frontend)

    @access.admin
    @filtermodel(model='frontend', plugin='ythub')
    @describeRoute(
        Description('Create a new frontend.')
        .notes('The output image is placed in the same parent folder as the '
               'input image.')
        .param('imageName', 'A docker image name.')
        .param('command', 'The main command run inside the container.',
               required=False)
        .param('memLimit', 'Impose RAM limit for the running container.',
               required=False)
        .param('user', 'User that will be running session inside '
               'the container.', required=False)
        .param('port', 'Bind specified within-container port.',
               required=False)
        .param('description', 'Short info about the image content.',
               required=False)
        .param('cpuShares', 'Limit cpu usage.', required=False)
    )
    def createFrontend(self, params):
        self.requireParams(('imageName'), params)

        command = params.get('command')
        memLimit = params.get('memLimit', '1024m')   # TODO: validate me
        imageName = params['imageName']
        user = params.get('user')
        port = params.get('port')
        description = params.get('description')
        cpuShares = params.get('cpuShares')

        return self.model('frontend', 'ythub').createFrontend(
            imageName, memLimit=memLimit, command=command, user=user,
            port=port, cpuShares=cpuShares, description=description)

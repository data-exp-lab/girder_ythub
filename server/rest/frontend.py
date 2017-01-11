#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.docs import addModel
from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, loadmodel, filtermodel
from girder.constants import AccessType, SortDir


frontendModel = {
    'id': 'frontend',
    'type': 'object',
    'required': [
        '_accessLevel', '_id', '_modelType', 'imageName',
        'description'
    ],
    'example': {
        '_accessLevel': 2,
        '_id': '5873dcdbaec030000144d233',
        '_modelType': 'frontend',
        'command': 'jupyter lab --no-browser',
        'cpuShares': '',
        'created': '2017-01-09T18:56:27.262000+00:00',
        'description': 'Run Jupyter Lab',
        'imageName': 'xarthisius/ythub-jupyter',
        'memLimit': '1024m',
        'port': '8888',
        'public': True,
        'updated': '2017-01-10T16:15:17.313000+00:00',
        'user': 'jovyan'
    },
    'properties': {
        '_accessLevel': {'type': 'integer', 'format': 'int32'},
        '_id': {'type': 'string'},
        '_modelType': {'type': 'string'},
        'imageName': {'type': 'string', 'allowEmptyValue': False},
        'command': {'type': 'string', 'allowEmptyValue': True},
        'memLimit': {'type': 'string', 'allowEmptyValue': True},
        'cpuShares': {'type': 'string', 'allowEmptyValue': True},
        'description': {'type': 'string', 'allowEmptyValue': False},
        'port': {'type': 'integer', 'format': 'int32',
                 'allowEmptyValue': True,
                 'maximum': 65535, 'minimum': 1},
        'updated': {'type': 'string', 'format': 'date',
                    'allowEmptyValue': True},
        'created': {'type': 'string', 'format': 'date',
                    'allowEmptyValue': True},
        'public': {'type': 'boolean', 'allowEmptyValue': True},
    }
}
addModel('frontend', frontendModel, resources='frontend')


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
        .responseClass('frontend', array=True)
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
        .responseClass('frontend')
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
        .param('public', 'Whether the frontend should be publicly visible.'
               ' Defaults to False.', dataType='boolean', required=False)
        .param('cpuShares', 'Limit cpu usage.', required=False)
        .responseClass('frontend')
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

        public = self.boolParam('public', params, default=False)
        self.model('frontend', 'ythub').setPublic(frontend, public)
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
        .param('public', 'Whether the frontend should be publicly visible.'
               ' Defaults to False.', dataType='boolean', required=False)
        .param('cpuShares', 'Limit cpu usage.', required=False)
        .responseClass('frontend')
        .errorResponse('You are not authorized to create collections.', 403)
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
        public = self.boolParam('public', params, default=None)

        return self.model('frontend', 'ythub').createFrontend(
            imageName, memLimit=memLimit, command=command, user=user,
            port=port, cpuShares=cpuShares, description=description,
            public=public)

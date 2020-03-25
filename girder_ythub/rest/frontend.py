#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.docs import addModel
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, filtermodel
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
    """Frontend resource."""

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
    @autoDescribeRoute(
        Description('List available frontends.')
        .responseClass('frontend', array=True)
        .pagingParams(defaultSort='imageName',
                      defaultSortDir=SortDir.DESCENDING)
    )
    def listFrontends(self, limit, offset, sort, params):
        user = self.getCurrentUser()
        return list(self.model('frontend', 'ythub').list(
            user=user, offset=offset, limit=limit, sort=sort))

    @access.user
    @filtermodel(model='frontend', plugin='ythub')
    @autoDescribeRoute(
        Description('Get a frontend by ID.')
        .modelParam('id', model='frontend', plugin='ythub',
                    level=AccessType.READ)
        .responseClass('frontend')
        .errorResponse('ID was invalid.')
    )
    def getFrontend(self, frontend, params):
        return frontend

    @access.admin
    @autoDescribeRoute(
        Description('Update an existing frontend.')
        .modelParam('id', model='frontend', plugin='ythub',
                    level=AccessType.WRITE)
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
        .param('targetMount', 'Path where data will be mounted.',
               required=False)
        .param('urlPath', 'Optional suffix to frontend url',
               required=False)
        .responseClass('frontend')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the frontend.', 403)
    )
    def updateFrontend(self, frontend, imageName, command, memLimit,
                       user, port, description, public, cpuShares,
                       targetMount, urlPath, params):
        frontend['imageName'] = imageName or frontend['imageName']
        frontend['command'] = command or frontend['command']
        frontend['memLimit'] = memLimit or frontend['memLimit']
        frontend['user'] = user or frontend['user']
        frontend['port'] = port or frontend['port']
        frontend['description'] = description or frontend['description']
        frontend['cpuShares'] = cpuShares or frontend['cpuShares']
        frontend['targetMount'] = targetMount or frontend['targetMount']
        frontend['urlPath'] = urlPath or frontend['urlPath']

        if public is not None:
            self.model('frontend', 'ythub').setPublic(frontend, public)
        return self.model('frontend', 'ythub').updateFrontend(frontend)

    @access.admin
    @autoDescribeRoute(
        Description('Delete an existing frontend.')
        .modelParam('id', model='frontend', plugin='ythub',
                    level=AccessType.WRITE)
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the frontend.', 403)
    )
    def deleteFrontend(self, frontend, params):
        self.model('frontend', 'ythub').remove(frontend)

    @access.admin
    @filtermodel(model='frontend', plugin='ythub')
    @autoDescribeRoute(
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
        .param('targetMount', 'Path where data will be mounted.',
               required=True)
        .param('urlPath', 'Optional suffix to frontend url',
               required=False, default='')
        .param('public', 'Whether the frontend should be publicly visible.'
               ' Defaults to False.', dataType='boolean', required=False)
        .param('cpuShares', 'Limit cpu usage.', required=False)
        .responseClass('frontend')
        .errorResponse('You are not authorized to create collections.', 403)
    )
    def createFrontend(self, imageName, command, memLimit, user, port,
                       description, public, cpuShares, targetMount, urlPath,
                       params):
        return self.model('frontend', 'ythub').createFrontend(
            imageName, memLimit=memLimit, command=command, user=user,
            port=port, cpuShares=cpuShares, description=description,
            public=public, urlPath=urlPath, targetMount=targetMount)

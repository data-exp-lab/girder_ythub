#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, loadmodel, filtermodel
from girder.constants import AccessType, SortDir


class Frontend(Resource):

    def __init__(self):
        super(Resource, self).__init__()
        self.resourceName = 'frontend'

        self.route('GET', (), self.listFrontends)
        self.route('GET', (':id',), self.getFrontend)
        self.route('POST', (':id',), self.createFrontend)
        self.route('DELETE', (':id',), self.deleteFrontend)

    @access.public
    @filtermodel(model='frontend', plugin='ythub')
    @describeRoute(
        Description('List available frontends.')
        .pagingParams(defaultSort='imageName',
                      defaultSortDir=SortDir.DESCENDING)
    )
    def listFrontends(self, params):
        limit, offset, sort = self.getPagingParameters(
            params, 'imageName', SortDir.DESCENDING)

        currentUser = self.getCurrentUser()
        return list(self.model('frontend', 'ythub').list(
            user=None, offset=offset, limit=limit, sort=sort,
            currentUser=currentUser))

    @access.public
    @filtermodel(model='frontend', plugin='ythub')
    @loadmodel(model='frontend', plugin='ythub', level=AccessType.NONE)
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
        .param('imageName', 'A docker image name')
    )
    def createFrontend(self, frontend, params):
        self.requireParams(('imageName'), params)

        return self.model('frontend', 'ythub').createFrontend(
            params['imageName'])

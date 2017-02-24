#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.docs import addModel
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, filtermodel, RestException
from girder.constants import AccessType, SortDir
from ..constants import containerConfigSchema

taleModel = {
    "description": "Object representing a Tale.",
    "required": [
        "_id",
        "folderId",
        "imageId"
    ],
    "properties": {
        "_id": {
            "type": "string",
            "description": "internal unique identifier"
        },
        "name": {
            "type": "string",
            "description": "A user-friendly name"
        },
        "description": {
            "type": "string"
        },
        "imageId": {
            "type": "string",
            "description": "ID of a WT Image used by the Tale"
        },
        "folderId": {
            "type": "string",
            "description": "ID of a data folder used by the Tale"
        },
        "public": {
            "type": "boolean",
            "description": "If set to true the Tale is accessible by anyone.",
            "default": True
        },
        "published": {
            "type": "boolean",
            "default": False,
            "description": "If set to true the Tale cannot be deleted or made unpublished."
        },
        "config": {
            "$ref": "#/definitions/containerConfig"
        },
        "created": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the tale was created."
        },
        "creatorId": {
            "type": "string",
            "description": "A unique identifier of the user that created the tale."
        },
        "updated": {
            "type": "string",
            "format": "date-time",
            "description": "The last time when the tale was modified."
        }
    },
    'example': {
        '_accessLevel': 2,
        '_id': '5873dcdbaec030000144d233',
        'creatorId': '5873dcdbaec030000144d233',
        'imageId': '5873dcdbaec030000144d233',
        'folderId': '5873dcdbaec030000144d233',
        'config': 'null',
        '_modelType': 'tale',
        'created': '2017-01-09T18:56:27.262000+00:00',
        'name': 'Jupyter Lab',
        'description': 'Run Jupyter Lab',
        'public': True,
        'published': True,
        'updated': '2017-01-10T16:15:17.313000+00:00',
    },
}
addModel('tale', taleModel, resources='tale')


class Tale(Resource):

    def __init__(self):
        super(Tale, self).__init__()
        self.resourceName = 'tale'

        self.route('GET', (), self.listTales)
        self.route('GET', (':id',), self.getTale)
        self.route('PUT', (':id',), self.updateTale)
        self.route('POST', (), self.createTale)
        self.route('DELETE', (':id',), self.deleteTale)

    @access.public
    @filtermodel(model='tale', plugin='ythub')
    @autoDescribeRoute(
        Description('Return all the tales accessible to the user')
        .param('imageId', "The ID of the tale's image.", required=False)
        .param('folderId', "The ID of the tale's folder.", required=False)
        .param('text', ('Perform a full text search for recipe with matching '
                        'name or description.'), required=False)
        .responseClass('tale', array=True)
        .pagingParams(defaultSort='lowerName',
                      defaultSortDir=SortDir.DESCENDING)
    )
    def listTales(self, imageId, folderId, text, limit, offset, sort, params):
        user = self.getCurrentUser()
        if imageId:
            image = self.model('image', 'ythub').load(
                imageId, user=user, level=AccessType.READ, exc=True)
        else:
            image = None

        if folderId:
            folder = self.model('folder').load(
                folderId, user=user, level=AccessType.READ, exc=True)
        else:
            folder = None

        if text:
            return list(self.model('tale', 'ythub').textSearch(
                text, user=user, limit=limit, offset=offset, sort=sort))
        else:
            return list(self.model('tale', 'ythub').list(
                user=user, folder=folder, image=image, currentUser=user,
                offset=offset, limit=limit, sort=sort))

    @access.public
    @filtermodel(model='tale', plugin='ythub')
    @autoDescribeRoute(
        Description('Get a tale by ID.')
        .modelParam('id', model='tale', plugin='ythub', level=AccessType.READ)
        .responseClass('tale')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the tale.', 403)
    )
    def getTale(self, tale, params):
        return tale

    @access.user
    @autoDescribeRoute(
        Description('Update an existing tale.')
        .modelParam('id', model='tale', plugin='ythub', level=AccessType.WRITE)
        .param('name', 'A name of the tale.', required=False)
        .param('description', 'A description of the tale', required=False)
        .param('public', 'Whether the tale should be publicly visible.',
               dataType='boolean', required=False)
        .param('published', 'If set to true, the Tale cannot be deleted or '
               'made unpublished.', dataType='boolean', required=False)
        .jsonParam('config', "The tale's runtime configuration",
                   required=False, schema=containerConfigSchema,
                   paramType='body')
        .responseClass('tale')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the tale.', 403)
    )
    def updateTale(self, tale, name, description, public, published, config, params):
        taleModel = self.model('tale', 'ythub')
        if description:
            tale['description'] = description
        if name:
            tale['name'] = name
        if config:
            tale['config'].update(config)
        if public is not None:
            taleModel.setPublic(tale, public)
        if published is not None:
            taleModel.setPublished(tale, published)
        return taleModel.updateTale(tale)

    @access.admin
    @autoDescribeRoute(
        Description('Delete an existing tale.')
        .modelParam('id', model='tale', plugin='ythub', level=AccessType.ADMIN)
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the tale.', 403)
    )
    def deleteTale(self, tale, params):
        self.model('tale', 'ythub').remove(tale)

    @access.user
    @autoDescribeRoute(
        Description('Create a new tale.')
        .param('imageId', 'The ID of an image used to build the tale.',
               required=False)
        .param('folderId', 'The ID of a folder used to build the tale.',
               required=False)
        .param('instanceId', 'The ID of a running instance to save as a tale.',
               required=False)
        .param('name', 'A name of the tale.', required=False)
        .param('description', 'A description of the tale.', required=False)
        .param('public', 'Whether the tale should be publicly visible.'
               ' Defaults to True.', dataType='boolean', required=False,
               default=True)
        .jsonParam('config', "The tale's runtime configuration",
                   required=False, schema=containerConfigSchema,
                   paramType='body')
        .responseClass('tale')
        .errorResponse('You are not authorized to create collections.', 403)
    )
    def createTale(self, imageId, folderId, instanceId, name, description,
                   public, config, params):

        user = self.getCurrentUser()
        if instanceId:
            # check if instance exists
            # save disk state to a new folder
            # save config
            # create a tale
            raise RestException('Not implemented yet')
        elif all((imageId, folderId)):
            image = self.model('image', 'ythub').load(
                imageId, user=user, level=AccessType.READ, exc=True)
            folder = self.model('folder').load(
                folderId, user=user, level=AccessType.READ, exc=True)
            return self.model('tale', 'ythub').createTale(
                image, folder, creator=user, save=True, name=name,
                description=description, public=public, config=config,
                published=False)
        else:
            raise RestException(
                'You need to specify either an "instanceId" or'
                ' an "imageId" and a "folderId".')

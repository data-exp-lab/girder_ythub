#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.docs import addModel
from girder.api.rest import Resource, filtermodel
from girder.constants import AccessType, SortDir


instanceModel = {
    'id': 'instance',
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
        '_modelType': 'instance',
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
addModel('instance', instanceModel, resources='instance')


class Instance(Resource):

    def __init__(self):
        super(Instance, self).__init__()
        self.resourceName = 'instance'

        self.route('GET', (), self.listInstances)
        self.route('POST', (), self.createInstance)
        self.route('GET', (':id',), self.getInstance)
        self.route('DELETE', (':id',), self.deleteInstance)

    @access.user
    @filtermodel(model='instance', plugin='wholetale')
    @autoDescribeRoute(
        Description('Return all the running instances accessible by the user')
        .param('taleId',  'List all the instanes using this tale.', required=False)
        .param('text', 'Perform a full text search for a tale with a matching '
               'name.', required=False)
        .responseClass('instance', array=True)
        .pagingParams(defaultSort='created', defaultSortDir=SortDir.DESCENDING)
    )
    def listInstances(self, taleId, text, limit, offset, sort, params):
        user = self.getCurrentUser()
        if taleId:
            tale = self.model('tale', 'wholetale').load(
                taleId, user=user, level=AccessType.READ)
        else:
            tale = None
        # TODO allow to search for instances that belongs to specific user
        return list(self.model('instance', 'wholetale').list(
            user=user, tale=tale, offset=offset, limit=limit,
            sort=sort, currentUser=user))

    @access.user
    @autoDescribeRoute(
        Description('Get an instance by ID.')
        .modelParam('id', model='instance', plugin='wholetale', level=AccessType.READ)
        .responseClass('instance')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the instance.', 403)
    )
    def getInstance(self, instance, params):
        return instance

    @access.user
    @autoDescribeRoute(
        Description('Delete an existing instance.')
        .modelParam('id', model='instance', plugin='wholetale', level=AccessType.WRITE)
        .errorResponse('ID was invalid.')
        .errorResponse('Write access was denied for the instance.', 403)
    )
    def deleteInstance(self, instance, params):
        self.model('instance', 'wholetale').deleteInstance(
            instance, self.getCurrentToken())

    @access.user
    @autoDescribeRoute(
        Description('Create a new instance')
        .notes('Instantiate a tale.')
        .param('taleId', 'The ID of a tale used to create an instance.',
               required=True)
        .param('name', 'A user-friendly, short name of the tale.',
               required=False)
        .responseClass('instance')
        .errorResponse('Read access was denied for the tale.', 403)
    )
    def createInstance(self, taleId, name, params):
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        tale = self.model('tale', 'wholetale').load(
            taleId, user=user, level=AccessType.READ)

        instanceModel = self.model('instance', 'wholetale')
        return instanceModel.createInstance(tale, user, token, save=True)

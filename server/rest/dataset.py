#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.docs import addModel
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource
from girder.constants import AccessType, SortDir
from girder.models.model_base import ValidationException
from .harvester import getOrCreateCatalogFolder

datasetModel = {
    "description": "Object representing registered data.",
    "required": [
        "_id",
        "modelType"
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
        "modelType": {
            "type": "string",
            "description": "Model of the object.",
            "enum": [
                "folder",
                "item"
            ]
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
        },
        "size": {
            "type": "integer",
            "description": "Total size of the dataset in bytes."
        },
        "identifier": {
            "type": "string",
            "description": "External, unique identifier"
        },
        "provider": {
            "type": "string",
            "description": "Name of the provider",
            "enum": [
                "DataONE",
                "HTTP",
                "Globus"
            ]
        }
    }
}
datasetModelKeys = set(datasetModel['properties'].keys())
addModel('dataset', datasetModel, resources='dataset')


def _itemOrFolderToDataset(obj):
    ds = {key: obj[key] for key in obj.keys() & datasetModelKeys}
    ds['provider'] = obj['meta']['provider']
    ds['identifier'] = obj['meta']['identifier']
    ds['modelType'] = obj['_modelType']
    return ds


class Dataset(Resource):

    def __init__(self):
        super(Dataset, self).__init__()
        self.resourceName = 'dataset'

        self.route('GET', (), self.listDatasets)
        self.route('GET', (':id',), self.getDataset)

    @access.public
    @autoDescribeRoute(
        Description(('Returns all registered datasets from the system '
                     'that user has access to'))
        .responseClass('dataset', array=True)
        .param('text', 'Perform a full text search for image with a matching '
               'name or description.', required=False)
        .pagingParams(defaultSort='lowerName',
                      defaultSortDir=SortDir.DESCENDING)
    )
    def listDatasets(self, text, limit, offset, sort, params):
        user = self.getCurrentUser()
        folderModel = self.model('folder')
        datasets = []

        parent = getOrCreateCatalogFolder()
        for folder in folderModel.childFolders(
                parentType='folder', parent=parent, user=user,
                limit=limit, offset=offset, sort=sort):
            datasets.append(_itemOrFolderToDataset(folder))

        for item in folderModel.childItems(
                folder=folder, limit=limit, offset=offset, sort=sort):
            datasets.append(_itemOrFolderToDataset(item))
        return datasets

    def _getResource(self, id, type):
        model = self._getResourceModel(type)
        return model.load(id=id, user=self.getCurrentUser(), level=AccessType.READ)

    @access.public
    @autoDescribeRoute(
        Description('Get any registered dataset by ID.')
        .param('id', 'The ID of the Dataset.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the resource.', 403)
    )
    def getResource(self, id, type, params):
        user = self.getCurrentUser()
        try:
            doc = self.model('folder').load(id=id, user=user, level=AccessType.READ, exc=True)
        except ValidationException:
            doc = self.model('item').load(id=id, user=user, level=AccessType.READ, exc=True)
        return _itemOrFolderToDataset(doc)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import boundHandler, RestException
from girder.constants import AccessType, TokenScope
from girder.utility.progress import ProgressContext
# from .constants import HarvesterType
from .dataone_harvester import DataONEHarvester

# http://blog.crossref.org/2015/08/doi-regular-expressions.html
_DOI_REGEX = re.compile('(10.\d{4,9}/[-._;()/:A-Z0-9]+)', re.IGNORECASE)


@access.admin(scope=TokenScope.DATA_WRITE)
@boundHandler()
@describeRoute(
    Description('Import existing data into an assetstore.')
    .notes('This does not move or copy the existing data, it just creates '
           'references to it in the Girder data hierarchy. Deleting '
           'those references will not delete the underlying data. This '
           'operation is currently only supported for S3 assetstores.')
    .param('doi', 'Root path within the underlying storage system '
           'to import.', required=True)
    .param('destinationId', 'ID of a folder, collection, or user in Girder '
           'under which the data will be imported.')
    .param('destinationType', 'Type of the destination resource.',
           enum=('folder', 'collection', 'user'))
    .param('progress', 'Whether to record progress on the import.',
           dataType='boolean', default=False, required=False)
    .errorResponse()
    .errorResponse('You are not an administrator.', 403)
)
def importData(self, params):
    self.requireParams(('destinationId', 'destinationType', 'doi'), params)

    parentType = params.pop('destinationType')
    if parentType not in ('folder', 'collection', 'user'):
        raise RestException(
            'The destinationType must be user, folder, or collection.')

    user = self.getCurrentUser()
    parent = self.model(parentType).load(
        params.pop('destinationId'), user=user, level=AccessType.ADMIN,
        exc=True)

    progress = self.boolParam('progress', params, default=False)
    doi = _DOI_REGEX.search(params.pop('doi'))
    if doi is None:
        raise RestException('Invalid DOI')
    doi = 'doi:' + doi.group()
    with ProgressContext(progress, user=user, title='Importing data') as ctx:
        harvester = DataONEHarvester('DataONE', doi)
        return harvester.ingestUrn(parent=parent, parentType=parentType,
                                   progress=ctx, user=user)

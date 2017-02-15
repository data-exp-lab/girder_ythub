#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource
from ..register_dataone import lookup

# http://blog.crossref.org/2015/08/doi-regular-expressions.html
_DOI_REGEX = re.compile('(10.\d{4,9}/[-._;()/:A-Z0-9]+)', re.IGNORECASE)


class Repository(Resource):

    def __init__(self):
        super(Repository, self).__init__()
        self.resourceName = 'repository'

        self.route('GET', ('lookup',), self.lookupData)

    @access.public
    @autoDescribeRoute(
        Description('Create data mapping to an external repository.')
        .notes('Given a list of external data identifiers, '
               'returns mapping to specific repository '
               'along with a basic metadata, such as size, name.')
        .param('dataId', dataType='array', paramType='query', required=True,
               description='List of external datasets identificators.')
        .responseClass('DataMap', array=True))
    def lookupData(self, params):
        return [lookup(path) for path in params['dataId']]

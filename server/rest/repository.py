#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import requests
import time
from urllib.parse import urlparse
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.docs import addModel
from girder.api.rest import Resource
from ..dataone_register import D1_lookup


dataMap = {
    'type': 'object',
    'description': ('A container with a basic information about '
                    'a set of external data resources.'),
    'properties': {
        'dataId': {
            'type': 'string',
            'description': 'External dataset identificator, such as URL.'
        },
        'repository': {
            'type': 'string',
            'description': 'Name of a data repository holding the dataset.'
        },
        'doi': {
            'type': 'string',
            'description': 'Digital Object Identifier'
        },
        'name': {
            'type': 'string',
            'description': ('A user-friendly name. Defaults to the name '
                            'provided by an external repository.')
        },
        'size': {
            'type': 'integer',
            'description': 'Size of the dataset in bytes.'
        }
    },
    'required': ['dataId', 'repository', 'doi', 'name', 'size'],
    'example': {
        'dataId': 'urn:uuid:42969280-e11c-41a9-92dc-33964bf785c8',
        'doi': '10.5063/F1Z899CZ',
        'name': ('Data from a dynamically downscaled projection of past and '
                 'future microclimates covering North America from 1980-1999 '
                 'and 2080-2099'),
        'repository': 'DataONE',
        'size': 178679
    },
}
addModel('dataMap', dataMap)


def _http_lookup(pid):
    url = urlparse(pid)
    if url.scheme not in ('http', 'https'):
        return
    headers = requests.head(pid).headers

    valid_target = headers.get('Content-Type') in \
        ('application/octet-stream', 'text/plain')
    valid_target = valid_target and 'Content-Length' in headers
    if not valid_target:
        return

    if 'Content-Disposition' in headers:
        fname = re.search('^.*filename=([\w.]+).*$',
                          headers['Content-Disposition'])
        if fname:
            fname = fname.groups()[0]
    else:
        fname = os.path.basename(url.path.rstrip('/'))

    return dict(dataId=pid, doi='unknown', name=fname, repository='HTTP',
                size=int(headers['Content-Length']))


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
        .jsonParam('dataId', paramType='query', required=True,
                   description='List of external datasets identificators.')
        .responseClass('dataMap', array=True))
    def lookupData(self, dataId, params):
        from concurrent.futures import ThreadPoolExecutor
        pool = ThreadPoolExecutor(len(dataId) * 2)

        futures = []
        for pid in dataId:
            futures.append(pool.submit(D1_lookup, (pid)))
            futures.append(pool.submit(_http_lookup, (pid)))

        while not all([_.done() for _ in futures]):
            time.sleep(0.2)
        return [_.result() for _ in futures if _.result()]

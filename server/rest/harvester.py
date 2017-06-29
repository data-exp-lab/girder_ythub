#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
import requests
from urllib.parse import urlparse

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import boundHandler, RestException, filtermodel
from girder.constants import AccessType, TokenScope
from girder.utility.model_importer import ModelImporter
from girder.utility import path as path_util
from girder.utility.progress import ProgressContext
from ..dataone_register import \
    D1_BASE, \
    esc, \
    get_aggregated_identifiers,\
    get_documenting_identifiers, \
    query, \
    unesc
from ..constants import dataMapListSchema


@access.user(scope=TokenScope.DATA_WRITE)
@autoDescribeRoute(
    Description('Create a folder containing references to an external data')
    .notes('This does not upload or copy the existing data, it just creates '
           'references to it in the Girder data hierarchy. Deleting '
           'those references will not delete the underlying data. This '
           'operation is currently only supported for DataONE repositories.\n'
           'If the parentId and the parentType is not provided, data will be '
           'registered into home directory of the user calling the endpoint')
    .param('parentId', 'Parent ID for the new parent of this folder.',
           required=False)
    .param('parentType', "Type of the folder's parent", required=False,
           enum=['folder', 'user', 'collection'], strip=True, default='folder')
    .param('public', 'Whether the folder should be publicly visible. '
           'Defaults to True.',
           required=False, dataType='boolean', default=True)
    .jsonParam('dataMap', 'A list of data mappings',
               paramType='body', schema=dataMapListSchema)
    .errorResponse('Write access denied for parent collection.', 403)
)
@boundHandler()
def importData(self, parentId, parentType, public, dataMap, params):
    user = self.getCurrentUser()

    if not parentId:
        parent = path_util.lookUpPath('/user/%s/Data' % user['login'], user)
        parentType = parent['model']
        parent = parent['document']
    else:
        parent = self.model(parentType).load(
            parentId, user=user, level=AccessType.WRITE, exc=True)

    progress = True
    with ProgressContext(progress, user=user,
                         title='Registering resources') as ctx:
        for data in dataMap:
            if data['repository'] == 'DataONE':
                process_package(parent, parentType, ctx, user,
                                data['dataId'], name=data['name'])
            elif data['repository'] == 'HTTP':
                register_http_resource(parent, parentType, ctx, user,
                                       data['dataId'], name=data['name'])
    return parent


def register_http_resource(parent, parentType, progress, user, url, name=None):
    progress.update(increment=1, message='Processing file {}.'.format(url))
    headers = requests.head(url).headers

    if not name:
        if 'Content-Disposition' in headers:
            name = re.search('^.*filename=([\w.]+).*$',
                             headers['Content-Disposition'])
            if name:
                name = name.groups()[0]
        else:
            name = os.path.basename(urlparse(url).path.rstrip('/'))

    fileModel = ModelImporter.model('file')
    fileDoc = fileModel.createLinkFile(
        url=url, parent=parent, name=name, parentType=parentType,
        creator=user, size=int(headers['Content-Length']),
        mimeType=headers['Content-Type'])
    gc_file = fileModel.filter(fileDoc, user)

    gc_item = ModelImporter.model('item').load(
        gc_file['itemId'], force=True)
    gc_item['meta'] = {'identifier': 'unknown'}
    gc_item = ModelImporter.model('item').updateItem(gc_item)


def process_package(parent, parentType, progress, user, pid, name=None):
    """Create a package description (Dict) suitable for dumping to JSON."""
    progress.update(increment=1, message='Processing package {}.'.format(pid))

    # query for things in the resource map
    result = query("resourceMap:\"{}\"".format(esc(pid)),
                   ["identifier", "formatType", "title", "size", "formatId",
                    "fileName", "documents"])

    if 'response' not in result or 'docs' not in result['response']:
        raise RestException(
            "Failed to get a result for the query\n {}".format(result))

    docs = result['response']['docs']

    # Filter the Solr result by TYPE so we can construct the package
    metadata = [doc for doc in docs if doc['formatType'] == 'METADATA']
    data = [doc for doc in docs if doc['formatType'] == 'DATA']
    children = [doc for doc in docs if doc['formatType'] == 'RESOURCE']

    # Verify what's in Solr is matching
    aggregation = get_aggregated_identifiers(pid)
    pids = set([unesc(doc['identifier']) for doc in docs])

    if aggregation != pids:
        raise RestException(
            "The contents of the Resource Map don't match what's in the Solr "
            "index. This is unexpected and unhandled.")

    # Find the primary/documenting metadata so we can later on find the
    # folder name
    # TODO: Grabs the resmap a second time, fix this
    documenting = get_documenting_identifiers(pid)

    # Stop now if multiple objects document others
    if len(documenting) != 1:
        raise RestException(
            "Found two objects in the resource map documenting other objects. "
            "This is unexpected and unhandled.")

    # Add in URLs to resolve each metadata/data object by
    for i in range(len(metadata)):
        metadata[i]['url'] = \
            "{}/resolve/{}".format(D1_BASE, metadata[i]['identifier'])

    for i in range(len(data)):
        data[i]['url'] = \
            "{}/resolve/{}".format(D1_BASE, data[i]['identifier'])

    # Determine the folder name. This is usually the title of the metadata file
    # in the package but when there are multiple metadata files in the package,
    # we need to figure out which one is the 'main' or 'documenting' one.
    primary_metadata = [doc for doc in metadata if 'documents' in doc]

    if len(primary_metadata) > 1:
        raise RestException("Multiple documenting metadata objects found. "
                            "This isn't implemented.")

    # Create a Dict to store folders' information
    # the data key is a concatenation of the data and any metadata objects
    # that aren't the main or documenting metadata

    data += [doc for doc in metadata
             if doc['identifier'] != primary_metadata[0]['identifier']]
    if not name:
        name = primary_metadata[0]['title']

    gc_folder = ModelImporter.model('folder').createFolder(
        parent, name, description='',
        parentType=parentType, creator=user, reuseExisting=True)
    gc_folder = ModelImporter.model('folder').setMetadata(
        gc_folder, {'identifier': primary_metadata[0]['identifier'],
                    'provider': 'DataONE'})

    fileModel = ModelImporter.model('file')
    for fileObj in data:
        try:
            fileName = fileObj['fileName']
        except KeyError:
            fileName = fileObj['identifier']
        fileDoc = fileModel.createLinkFile(
            url=fileObj['url'], parent=gc_folder,
            name=fileName, parentType='folder',
            creator=user, size=int(fileObj['size']),
            mimeType=fileObj['formatId'])
        gc_file = fileModel.filter(fileDoc, user)

        gc_item = ModelImporter.model('item').load(
            gc_file['itemId'], force=True)
        gc_item['meta'] = {'identifier': fileObj['identifier']}
        gc_item = ModelImporter.model('item').updateItem(gc_item)

    # Recurse and add child packages if any exist
    if children is not None and len(children) > 0:
        for child in children:
            process_package(gc_folder, 'folder', progress, user,
                            child['identifier'])
    return gc_folder


@access.user(scope=TokenScope.DATA_READ)
@filtermodel(model='folder')
@autoDescribeRoute(
    Description('List all folders containing references to an external data')
    .errorResponse('Write access denied for parent collection.', 403)
)
@boundHandler()
def listImportedData(self, params):
    q = {'meta.provider': {'$exists': 1}}
    return list(ModelImporter.model('folder').find(query=q))

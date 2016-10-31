#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import xmltodict
import requests
import rdflib
import six.moves.urllib as urllib
from girder.utility.model_importer import ModelImporter

DATAONE_COLL_ID = '57fc1a1986ed1d000173b463'


def DataONE_url(suffix, api=2):
    return 'https://cn.dataone.org/cn/v{}/{}/'.format(api, suffix)


class DataONEHarvester(ModelImporter):

    def __init__(self, harvester, doi):
        # super(DataONEHarvester, self).__init__()
        self.harvester = harvester

        params = {
            'q': 'id:"{}"'.format(doi),
            'fl': ('id,resourceMap'),
            'wt': 'json'
        }
        r = requests.get('https://search.dataone.org/cn/v2/query/solr/',
                         params=params)
        search = r.json()

        # TODO check how many docs has been found
        document = search['response']['docs'][0]
        self.base_urn = document['resourceMap'][0]  # TODO check if exist

    def ingestUrn(self, parent, parentType, progress, user, urn=None):

        if urn is None:
            urn = self.base_urn

        progress.update(message=urn)
        g = rdflib.Graph()
        g.parse(DataONE_url('object', 1) + urn, format='xml')

        docBy_m = rdflib.term.URIRef(
            'http://purl.org/spar/cito/isDocumentedBy')
        agg_m = rdflib.term.URIRef(
            'http://www.openarchives.org/ore/terms/isAggregatedBy')
        agg_cur = rdflib.term.URIRef(
            'https://cn.dataone.org/cn/v1/resolve/{}#aggregation'.format(urn))

        all_urns = set(list(g.subjects(agg_m, agg_cur)))

        meta_docs = list(
            set([_[-1] for _ in list(g.subject_objects(docBy_m))]))
        for doc in meta_docs:
            doc_url = urllib.parse.unquote(doc.toPython())
            r = requests.get(doc_url)
            metadata = xmltodict.parse(r.content, process_namespaces=True)

            doi_set = set(list(g.subjects(docBy_m, doc)))
            remaining_urns = (all_urns - doi_set) - set([doc])
            # recurse over remaining_urns
            for urn in remaining_urns:
                urn_base = urllib.parse.unquote(
                    os.path.basename(urn.toPython()))
                self.ingestUrn(parent, parentType, urn_base, progress, user)

            namespace = list(metadata.keys())[0]
            meta = metadata[namespace]
            ds_title = meta['dataset']['title'].encode('utf8')
            ds_abstract = meta['dataset']['abstract'].encode('utf8')
            folder_description = '## {}\n\n{}'.format(ds_title, ds_abstract)
            gc_folder = self.model('folder').createFolder(
                parent, meta['@packageId'], description=folder_description,
                parentType=parentType, reuseExisting=True)

            folder_meta = dict((k, meta['dataset'][k])
                               for k in ('creator', 'pubDate', 'keywordSet'))
            folder_meta['doi'] = doc_url.split('doi:')[-1]
            gc_folder['meta'] = folder_meta
            gc_folder = self.model('folder').updateFolder(gc_folder)

            files_meta = [_['entityName']
                          for _ in meta['dataset']['otherEntity']]
            for subject in list(g.subjects(docBy_m, doc)):
                file_url = urllib.parse.unquote(subject.toPython())
                meta_url = DataONE_url('meta', api=2) + \
                    os.path.basename(file_url)
                r = requests.get(meta_url, allow_redirects=False)
                data = xmltodict.parse(r.content, process_namespaces=True)
                data_nm = list(data.keys())[0]
                try:
                    file_name = data[data_nm]['fileName']
                    file_size = data[data_nm]['size']
                except KeyError:
                    # why does it happen?!
                    print("file_url = {}".format(file_url))
                    continue
                file_meta = None
                for fn in (file_name, os.path.splitext(file_name)[0]):
                    try:
                        ind = files_meta.index(fn)
                        file_meta = meta['dataset']['otherEntity'][ind]
                    except ValueError:
                        continue

                if file_meta is None:
                    print("Something went wrong, catch this....")

                gc_file = self.model('file').filter(
                    self.model('file').createLinkFile(
                        url=file_url, parent=gc_folder, name=file_name,
                        parentType='folder', creator=user,
                        size=int(file_size)),
                    user)

                if file_meta is not None:
                    gc_item = self.model('item').load(gc_file['itemId'],
                                                      force=True)
                    gc_item['meta'] = file_meta
                    gc_item = self.model('item').updateItem(gc_item)

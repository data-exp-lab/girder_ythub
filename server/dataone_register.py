#!/usr/bin/env python

''' wt-regiser-dataone.py

A command-line utility intended to be a working demonstration of how a DataONE
dataset can be mapped to a file system.

The input to this tool is a string which is either a DataONE landing page URL or
A DataONE resolve/object URL.

This would be run like:

  python wt-register-dataone.py "urn:uuid:42969280-e11c-41a9-92dc-33964bf785c8"

which, after being run, would write a file in the working directory named like
'wt-package....json'.
'''

import re
import json
import six.moves.urllib as urllib
import requests
import rdflib

from girder.api.rest import RestException

# http://blog.crossref.org/2015/08/doi-regular-expressions.html
_DOI_REGEX = re.compile('(10.\d{4,9}/[-._;()/:A-Z0-9]+)', re.IGNORECASE)
D1_BASE = "https://cn.dataone.org/cn/v2"


def esc(value):
    """Escape a string so it can be used in a Solr query string"""

    return urllib.parse.quote_plus(value)


def unesc(value):
    """Unescapes a string so it can uesd in URLS"""
    return urllib.parse.unquote_plus(value)


def query(q, fields=["identifier"], rows=1000, start=0):
    """Query a DataONE Solr index."""

    fl = ",".join(fields)
    query_url = "{}/query/solr/?q={}&fl={}&rows={}&start={}&wt=json".format(
        D1_BASE, q, fl, rows, start)

    req = requests.get(query_url)
    content = json.loads(req.content.decode('utf8'))

    # Fail if the Solr query failed rather than fail later
    if content['responseHeader']['status'] != 0:
        raise RestException(
            "Solr query was not successful.\n{}\n{}".format(query_url, content))

    # Stop if the number of results is equal to the number of rows requested
    # Fix this in the future by supporting paginated queries.
    if content['response']['numFound'] == rows:
        raise RestException(
            "Number of results returned equals number of rows requested. "
            "This could mean the query result is truncated. "
            "Implement paged queries.")

    return content


def find_package_pid(pid):
    """Find the PID of the resource map for a given PID, which may be a resource
    map"""

    result = query(
        "identifier:\"{}\"".format(esc(pid)),
        fields=["identifier", "formatType", "formatId", "resourceMap"])
    result_len = int(result['response']['numFound'])

    if result_len == 0:
        raise RestException('No object was found in the index for {}.'.format(pid))
    elif result_len > 1:
        raise RestException(
            'More than one object was found in the index for the identifier '
            '{} which is an unexpected state.'.format(pid))

    # Find out if the PID is an OAI-ORE PID and return early if so
    if result['response']['docs'][0]['formatType'] == 'RESOURCE':
        return(result['response']['docs'][0]['identifier'])

    if len(result['response']['docs'][0]['resourceMap']) == 1:
        return result['response']['docs'][0]['resourceMap'][0]

    # Error out if the document passed in has multiple resource maps. What I can
    # still do here is determine the most likely resource map given the set.
    # Usually we do this by rejecting any obsoleted resource maps and that
    # usually leaves us with one.
    raise RestException(
        "Multiple resource maps were found and this is not implemented.")


def find_initial_pid(path):
    """Given some arbitrary path, which may be a landing page, resolve URI or
    something else, find the PID the user intended (the package PID).

    This can parse the PID out of the HTTP and HTTPS versions of...
        - The MetacatUI landing page (#view)
        - The D1 v2 Object URI (/object)
        - The D1 v2 Resolve URI (/resolve)
    """

    package_pid = None
    doi = _DOI_REGEX.search(path)

    if re.search(r'^http[s]?:\/\/search.dataone.org\/#view\/', path):
        package_pid = re.sub(
            r'^http[s]?:\/\/search.dataone.org\/#view\/', '', path)
    elif re.search(r'^http[s]?://cn.dataone.org/cn/d1/v[\d]/\w+/', path):
        package_pid = re.sub(
            r'^http[s]?://cn.dataone.org/cn/d1/v[\d]/\w+/', '', path)
    elif doi is not None:
        package_pid = 'doi:{}'.format(doi.group())
    else:
        package_pid = path

    return package_pid


def get_aggregated_identifiers(pid):
    """Process an OAI-ORE aggregation into a set of aggregated identifiers."""

    g = rdflib.Graph()

    graph_url = "{}/resolve/{}".format(D1_BASE, esc(pid))
    g.parse(graph_url, format='xml')

    ore_aggregates = rdflib.term.URIRef(
        'http://www.openarchives.org/ore/terms/aggregates')
    dcterms_identifier = rdflib.term.URIRef(
        'http://purl.org/dc/terms/identifier')

    aggregated = g.objects(None, ore_aggregates)

    pids = set()

    # Get the PID of the aggregated Objects in the package
    for object in aggregated:
        identifiers = g.objects(object, dcterms_identifier)
        [pids.add(unesc(id)) for id in identifiers]

    return pids


def get_documenting_identifiers(pid):
    """Find the set of identifiers in an OAI-ORE resource map documenting
    other members of that resource map."""

    g = rdflib.Graph()

    graph_url = "{}/resolve/{}".format(D1_BASE, esc(pid))
    g.parse(graph_url, format='xml')

    cito_isDocumentedBy = rdflib.term.URIRef(
        'http://purl.org/spar/cito/isDocumentedBy')
    dcterms_identifier = rdflib.term.URIRef(
        'http://purl.org/dc/terms/identifier')

    documenting = g.objects(None, cito_isDocumentedBy)

    pids = set()

    # Get the PID of the documenting Objects in the package
    for object in documenting:
        identifiers = g.objects(object, dcterms_identifier)
        [pids.add(unesc(id)) for id in identifiers]

    return pids


def lookup(path):
    """Create the map (JSON) describing a Data Package."""
    initial_pid = find_initial_pid(path)
    print("Parsed initial PID of {}.".format(initial_pid))

    package_pid = find_package_pid(initial_pid)
    print("Found package PID of {}.".format(package_pid))

    # query for things in the resource map
    result = query('resourceMap:"{}"'.format(esc(package_pid)),
                   ["identifier", "formatType", "title", "size", "formatId",
                    "fileName", "documents"])

    if 'response' not in result or 'docs' not in result['response']:
        raise RestException(
            "Failed to get a result for the query\n {}".format(result))

    docs = result['response']['docs']

    # Filter the Solr result by TYPE so we can construct the package
    metadata = [doc for doc in docs if doc['formatType'] == 'METADATA']
    if not metadata:
        raise RestException('No metadata found.')

    dataMap = {
        'dataId': package_pid,
        'size': metadata[0].get('size', -1),
        'name': metadata[0].get('title', 'no title'),
        'doi': metadata[0].get('identifier', 'no DOI').split('doi:')[-1],
        'repository': 'DataONE',
    }
    return dataMap

import cherrypy
import json
import time

from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, setResponseHeader
from girder.api import access


MOCK_DATA = [
    {
        'year': 2016,
        'title': ('BIONESS profile and plankton sample '
                  'collection data for plankton samples '
                  'collected off Alabama (2007-2015).'),
        'author': ('Gulf of Mexico Research Initiative '
                   'Information and Data Cooperative (GRIIDC)'),
        'doi': 'R2-x221-000-0007-004',
        'source': 'DataONE',
        'url': 'https://www.google.com/'
    },
    {
        'year': 2016,
        'author': 'Stephen Masutani',
        'title': ('Video recordings of jet break-up and '
                  'oil droplet dissolution and fractionation '
                  'during their buoyant rise through a column of '
                  'synthetic sea water.'),
        'doi': 'R1-x137-132-0001-003',
        'source': 'DataONE',
        'url': 'https://www.google.com/'
    },
    {
        'year': 2016,
        'author': 'Brian Dzwonkowski',
        'title': ('Fisheries Oceanography in Coastal Alabama (FOCAL) '
                  'Mooring data, January, April, and May 2011. '),
        'doi': 'Y1-x014-000-0003-0005',
        'source': 'globus',
        'url': 'https://www.google.com/'
    },
    {
        'year': 2016,
        'title': ('Shelf Regional Ocean Modeling System (ROMS-Shelf) '
                  '2003-2011 Hindcast for the Texas-Louisana Shelf.'),
        'author': ('Gulf of Mexico Research Initiative '
                   'Information and Data Cooperative (GRIIDC)'),
        'doi': 'R1-x137-108-0007-0003',
        'source': 'globus',
        'url': 'https://www.google.com/'
    }
]


def sseMessage(event):
    """
    Serializes an event into the server-sent events protocol.
    """
    return 'data: %s\n\n' % json.dumps(event, default=str)


class DatasetSearchEngine(Resource):

    def __init__(self):
        super(DatasetSearchEngine, self).__init__()
        self.resourceName = 'search'

        self.route('GET', ('global',), self.streamSearch)

    @access.public
    @describeRoute(
        Description('Stream search for data using all WT providers')
        .notes('This uses long-polling to keep the connection open for '
               'several minutes at a time (or longer) and should be requested '
               'with an EventSource object or other SSE-capable client. '
               '<p>Notifications are returned within a few seconds of when '
               'they occur.  When no notification occurs for the timeout '
               'duration, the stream is closed. '
               '<p>This connection can stay open indefinitely long.')
        .param('timeout', 'The duration without a notification before the '
               'stream is closed.', dataType='integer', required=False)
        .errorResponse()
        .errorResponse('You are not logged in.', 403)
    )
    def streamSearch(self, params):
        setResponseHeader('Content-Type', 'text/event-stream')
        setResponseHeader('Cache-Control', 'no-cache')

        def streamGen():
            for event in MOCK_DATA:
                yield sseMessage(event)
                time.sleep(1)

            setResponseHeader('Content-Type', 'application/json')
            cherrypy.response.status = 404
            # Any of the above should stop streaming but for some
            # reason it doesn't work with my simple client
            yield 'data: STOP\n\n'

        return streamGen

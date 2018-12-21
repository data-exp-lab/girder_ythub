from girder.api import access
from girder.api.describe import autoDescribeRoute, Description
from girder.api.rest import filtermodel, Resource
from girder.constants import AccessType
from girder.models.model_base import ValidationException


class Raft(Resource):
    """Raft resource."""

    def __init__(self):
        super(Raft, self).__init__()
        self.resourceName = 'raft'
        self.route('GET', (), self.listRafts)

    @access.public
    @autoDescribeRoute(
        Description('List all available rafts that can be executed.')
        .pagingParams(defaultSort='name')
    )
    @filtermodel(model='item')
    def listRafts(self, limit, offset, sort, params):
        cursor = self.model('item').find({
            'meta.isRaft': {'$exists': True}
        }, sort=sort)

        return list(self.model('item').filterResultsByPermission(
            cursor, self.getCurrentUser(), level=AccessType.READ,
            limit=limit, offset=offset))

    def _validateRaft(self, item):
        if 'raftSpec' not in item.get('meta'):
            raise ValidationException(
                'Item (%s) does not contain an raft specification.')
        spec = item['meta']['raftSpec']

        # perform validation

        return spec

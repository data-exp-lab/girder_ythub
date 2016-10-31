from .dataone_harvester import DataONEHarvester
from .constants import HarvesterType


_harvesterTable = {
    HarvesterType.DATAONE: DataONEHarvester
}


def getHarvesterAdapter(harvester, instance=True):
    harvesterType = harvester['type']
    cls = _harvesterTable.get(harvesterType)
    if cls is None:
        raise Exception('No AssetstoreAdapter for type: %s.' % harvesterType)

    if instance:
        return cls(harvester)
    else:
        return cls

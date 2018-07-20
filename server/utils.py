from girder.models.collection import Collection
from girder.models.folder import Folder


def getOrCreateRootFolder(name):
    collection = Collection().createCollection(
        name, public=True, reuseExisting=True)
    # For backward compat
    if not collection['public']:
        collection = Collection().save(
            Collection().setPublic(collection, True)
        )
    folder = Folder().createFolder(
        collection, name, parentType='collection', public=True, reuseExisting=True)
    return folder

from girder.utility.model_importer import ModelImporter


def getOrCreateRootFolder(name):
    collection = ModelImporter.model('collection').createCollection(
        name, public=False, reuseExisting=True)
    folder = ModelImporter.model('folder').createFolder(
        collection, name, parentType='collection', public=True, reuseExisting=True)
    return folder

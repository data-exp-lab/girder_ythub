girder.models.NotebookModel = girder.AccessControlledModel.extend({
    resourceName: 'notebook'
});

girder.collections.NotebookCollection = girder.Collection.extend({
    resourceName: 'notebook',
    model: girder.models.NotebookModel
});



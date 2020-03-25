import AccessControlledModel from 'girder/models/AccessControlledModel';

var NotebookModel = AccessControlledModel.extend({
    resourceName: 'notebook'
});

export default NotebookModel;

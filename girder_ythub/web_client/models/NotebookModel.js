import AccessControlledModel from '@girder/core/models/AccessControlledModel';

var NotebookModel = AccessControlledModel.extend({
    resourceName: 'notebook'
});

export default NotebookModel;

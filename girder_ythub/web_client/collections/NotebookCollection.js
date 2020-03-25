import Collection from 'girder/collections/Collection';

import NotebookModel from '../models/NotebookModel';

var NotebookCollection = Collection.extend({
    resourceName: 'notebook',
    model: NotebookModel
});

export default NotebookCollection;

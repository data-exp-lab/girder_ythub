import Collection from '@girder/core/collections/Collection';

import FrontendModel from '../models/FrontendModel';

var FrontendCollection = Collection.extend({
    resourceName: 'frontend',
    model: FrontendModel
});

export default FrontendCollection;

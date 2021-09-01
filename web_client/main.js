import GlobalNavView from 'girder/views/layout/GlobalNavView';
import { wrap } from 'girder/utilities/PluginUtils';

import './routes';
import './views/HierarchyWidget';
import './views/HeaderUserView';
import './views/FooterView';
import './views/ItemView';

// Add a new global nav item for creating and browsing rafts
wrap(GlobalNavView, 'initialize', function (initialize) {
    initialize.apply(this, arguments);

    this.defaultNavItems.push({
        name: 'Rafts',
        icon: 'icon-cubes',
        target: 'rafts'
    });
});

import GlobalNavView from '@girder/core/views/layout/GlobalNavView';
import { wrap } from '@girder/core/utilities/PluginUtils';

import './routes';
import './views/HierarchyWidget';
import './views/HeaderUserView';
import './views/FooterView';

// Add a new global nav item for creating and browsing rafts
wrap(GlobalNavView, 'initialize', function (initialize) {
    initialize.apply(this, arguments);

    this.defaultNavItems.push({
        name: 'Rafts',
        icon: 'icon-cubes',
        target: 'rafts'
    });
});

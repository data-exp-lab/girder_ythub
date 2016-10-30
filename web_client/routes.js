import router from 'girder/router';
import events from 'girder/events';
import { exposePluginConfig } from 'girder/utilities/PluginUtils';

exposePluginConfig('ythub', 'plugins/ythub/config');

import ConfigView from './views/ConfigView';
router.route('plugins/ythub/config', 'ythubConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});

import NotebookListWidget from './views/NotebookListWidget';
router.route('notebook/user/:id', 'notebookList', function (id) {
    events.trigger('g:navigateTo', NotebookListWidget, {
        filter: {userId: id}
    });
});

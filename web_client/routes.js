/* eslint-disable import/first */

import router from 'girder/router';
import events from 'girder/events';
import { exposePluginConfig } from 'girder/utilities/PluginUtils';
import ItemModel from 'girder/models/ItemModel';
import { Layout } from 'girder/constants';

import ConfigView from './views/ConfigView';
import NotebookListWidget from './views/NotebookListWidget';
import RaftListView from './views/RaftListView';
import RaftRunView from './views/RaftRunView';
import CreateRaftView from './views/body/CreateRaftView';
import FrontendModel from './models/FrontendModel';
import RunNotebookView from './views/RunNotebookView';

exposePluginConfig('ythub', 'plugins/ythub/config');

router.route('plugins/ythub/config', 'ythubConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});

router.route('notebook/user/:id', 'notebookList', function (id) {
    events.trigger('g:navigateTo', NotebookListWidget, {
        filter: {userId: id}
    });
});

router.route('rafts', 'raftList', () => {
    events.trigger('g:navigateTo', RaftListView);
});

router.route('raft/new', 'newRaft', () => {
    events.trigger('g:navigateTo', CreateRaftView);
});

router.route('raft/:id/run', (id, params) => {
    const item = new ItemModel({_id: id});
    const promises = [item.fetch()];

    $.when.apply($, promises).done(() => {
        events.trigger('g:navigateTo', RaftRunView, {
            model: item
        }, {
            renderNow: true
        });
    }).fail(() => {
        router.navigate('rafts', {trigger: true});
    });
});

router.route('raft/:id/edit', 'newRaft', (id, params) => {
    const itemTask = new ItemModel({_id: id});
    let frontend = null;
    const promises = [itemTask.fetch()];

    if (params.frontendId) {
        frontend = new FrontendModel({_id: params.frontendId});
        promises.push(frontend.fetch());
    }

    $.when(...promises).done(() => {
        let raftSpec = itemTask.get('meta').raftSpec;
        let initialValues = {
            data: raftSpec.data,
            frontendId: raftSpec.frontend,
            frontendName: frontend.get('description'),
            scripts: raftSpec.scripts
        };

        events.trigger('g:navigateTo', CreateRaftView, {
            model: itemTask,
            initialValues: initialValues
        }, {
            renderNow: true
        });
    }).fail(() => {
        router.navigate('rafts', {trigger: true, replace: true});
    });
});

router.route('frontend/:id/:folderId', 'runNotebook', function (id, folderId) {
    events.trigger('g:navigateTo', RunNotebookView, {
        frontendId: id,
        folderId: folderId
    }, {
        layout: Layout.EMPTY
    });
});

router.route('raft/:id', (id, params) => {
    const item = new ItemModel({_id: id});
    const promises = [item.fetch()];

    $.when.apply($, promises).done(() => {
        let raftSpec = item.get('meta').raftSpec;
        events.trigger('g:navigateTo', RunNotebookView, {
            frontendId: raftSpec.frontend,
            folderId: raftSpec.data,
            scripts: raftSpec.scripts
        }, {
            layout: Layout.EMPTY
        });
    }).fail(() => {
        router.navigate('rafts', {trigger: true});
    });
});

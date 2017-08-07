import View from 'girder/views/View';
import { renderMarkdown } from 'girder/misc';
import { restRequest } from 'girder/rest';
import router from 'girder/router';

import template from '../templates/raftRun.pug';
import '../stylesheets/raftRun.styl';

const RaftRunView = View.extend({
    events: {
        'click .g-run-raft': 'execute'
    },

    initialize: function (settings) {
        this._raftSpec = this.model.get('meta').raftSpec;
        const promises = [
            restRequest({
                path: 'resource/' + this._raftSpec.data + '/path',
                type: 'GET',
                data: {
                    type: 'folder'
                }
            }).then((resp) => resp),
            restRequest({
                path: 'frontend/' + this._raftSpec.frontend,
                type: 'GET'
            }).then((resp) => resp)
        ];
        this._raftSpec.scripts.forEach(function (element) {
            promises.push(
                restRequest({
                    path: 'resource/' + element + '/path',
                    type: 'GET',
                    data: {
                        type: 'item'
                    }
                }).then((resp) => resp)
            );
        });

        var view = this;

        // Fetch the plugin list
        $.when(...promises).done(function () {
            view.scripts = [];
            if (arguments.length > 2) {
                for (var i = 2; i < arguments.length; i++) {
                    view.scripts.push(arguments[i]);
                }
            }
            view.data = arguments[0];
            view.frontend = arguments[1]['description'];
            view.render();
        }).fail(() => {
            router.navigate('/', { trigger: true });
        });
    },

    render: function () {
        this.$el.html(template({
            item: this.model,
            data: this.data,
            frontend: this.frontend,
            scripts: this.scripts,
            renderMarkdown: renderMarkdown
        }));
    },

    execute: function (e) {
        console.log('Would run raft');
    }
});

export default RaftRunView;

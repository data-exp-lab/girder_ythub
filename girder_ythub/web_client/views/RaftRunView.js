import View from '@girder/core/views/View';
import { renderMarkdown } from '@girder/core/misc';
import { restRequest } from '@girder/core/rest';
import router from '@girder/core/router';

import template from '../templates/raftRun.pug';
import '../stylesheets/raftRun.styl';

const RaftRunView = View.extend({
    events: {
        'click .g-run-raft': 'execute',
        'click .g-edit-raft': function (event) {
            router.navigate('raft/' + this.model.get('_id') + '/edit?frontendId=' + this._raftSpec.frontend, {
                params: this._raftSpec,
                trigger: true
            });
        }
    },

    initialize: function (settings) {
        this._raftSpec = this.model.get('meta').raftSpec;
        const promises = [
            restRequest({
                url: 'resource/' + this._raftSpec.data + '/path',
                type: 'GET',
                data: {
                    type: 'folder'
                }
            }).then((resp) => resp),
            restRequest({
                url: 'frontend/' + this._raftSpec.frontend,
                type: 'GET'
            }).then((resp) => resp)
        ];
        this._raftSpec.scripts.forEach(function (element) {
            promises.push(
                restRequest({
                    url: 'resource/' + element + '/path',
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
            scripts: this.scripts || [],
            renderMarkdown: renderMarkdown
        }));
        return this;
    },

    execute: function (e) {
        // TODO Validate raft

        this.$('.g-validation-failed-message').empty();
        $(e.currentTarget).girderEnable(false);

        restRequest({
            url: 'notebook',
            method: 'POST',
            data: {
                folderId: this._raftSpec.data,
                frontendId: this._raftSpec.frontend,
                scripts: JSON.stringify(this._raftSpec.scripts)
            },
            error: null
        }).done((resp) => {
            window.location.assign(resp['url']);
        }).fail((resp) => {
            $(e.currentTarget).girderEnable(true);
            this.$('.g-validation-failed-message').text('Error: ' + resp.responseJSON.message);
        });
    }
});

export default RaftRunView;

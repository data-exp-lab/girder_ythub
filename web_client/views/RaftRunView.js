import View from 'girder/views/View';
import { renderMarkdown } from 'girder/misc';

import template from '../templates/raftRun.pug';
import '../stylesheets/raftRun.styl';

const RaftRunView = View.extend({
    events: {
        'click .g-run-raft': 'execute'
    },

    intialize: function (settings) {
        this._raftSpec = this.model.get('meta').raftSpec;
    },

    render: function () {
        this.$el.html(template({
            item: this.model,
            renderMarkdown: renderMarkdown
        }));
    },

    execute: function (e) {
        console.log('Would run raft');
    }
});

export default RaftRunView;

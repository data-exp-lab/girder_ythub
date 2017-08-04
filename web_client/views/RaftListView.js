import View from 'girder/views/View';

import PaginateRaftsWidget from './PaginateRaftsWidget';

var RaftListView = View.extend({
    initialize: function () {
        this.paginateWidget = new PaginateRaftsWidget({
            el: this.$el,
            parentView: this,
            itemUrlFunc: (raft) => {
                return `#raft/${raft.id}/run`;
            }
        });
    }
});

export default RaftListView;

import View from '@girder/core/views/View';
import PaginateWidget from '@girder/core/views/widgets/PaginateWidget';
import router from '@girder/core/router';

import RaftCollection from '../collections/RaftCollection';
import template from '../templates/paginateRaftsWidget.pug';
import '../stylesheets/paginateRaftsWidget.styl';

var PaginateRaftsWidget = View.extend({
    events: {
        'click .g-execute-raft-link': function (event) {
            const raftId = $(event.currentTarget).data('raftId');
            const raft = this.collection.get(raftId);
            this.trigger('g:selected', {
                raft: raft
            });
        },
        'click button.g-raft-create-button': function (event) {
            router.navigate('newraft', {trigger: true});
        }
    },
    /**
     * @param {Function} [settings.itemUrlFunc] A callback function, which if provided,
     *        will be called with a single ItemModel argument and should return a string
     *        URL to be used as the raft link href.
     * @param {RaftCollection} [settings.collection] An RaftCollection for the widget
     *        to display. If no collection is provided, a new RaftCollection is used.
     */
    initialize: function (settings) {
        this.itemUrlFunc = settings.itemUrlFunc || null;
        this.collection = settings.collection || new RaftCollection();
        this.paginateWidget = new PaginateWidget({
            collection: this.collection,
            parentView: this.parentView
        });

        this.listenTo(this.collection, 'g:changed', () => {
            this.render();
        });

        if (settings.collection) {
            this.render();
        } else {
            this.collection.fetch(this.params);
        }
    },

    render: function () {
        this.$el.html(template({
            rafts: this.collection.toArray(),
            itemUrlFunc: this.itemUrlFunc
        }));

        this.paginateWidget.setElement(this.$('.g-raft-pagination')).render();
        return this;
    }
});

export default PaginateRaftsWidget;

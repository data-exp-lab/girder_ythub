import { restRequest } from 'girder/rest';
import View from 'girder/views/View';

import RelatedSimsWidgetTemplate from '../templates/relatedSimsWidget.pug';

import '../stylesheets/relatedSimsWidget.styl';

var RelatedSimsWidget = View.extend({
    initialize: function (settings) {
        this.item = settings.item;
    },

    render: function () {
        var uuid = this.item.attributes.meta.conf.uuid;
        var widget = this;
        
        restRequest({
            url: "qmc",
            type: "GET",
            data: {configId: uuid},
            error: null
        }).done(function (sims) {
            console.log("I was here");
            console.log(this);
            console.log(widget);
            widget.$el.html(RelatedSimsWidgetTemplate({
                currentId: widget.item.attributes._id,
                sims: sims
            }));
        });
        return this;
    }
});

export default RelatedSimsWidget;

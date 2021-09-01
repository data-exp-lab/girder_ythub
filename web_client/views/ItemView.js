import ItemView from 'girder/views/body/ItemView';
import { wrap } from 'girder/utilities/PluginUtils';

import RelatedSimsWidget from './RelatedSimsWidget';
/**
 * Add an entry to the user dropdown menu to navigate to user's job list view.
 */
wrap(ItemView, 'render', function (render) {
    this.once('g:rendered', function () {
        var relatedSimsWidget = new RelatedSimsWidget({
            item: this.model,
            parentView: this
        }).render();

        $('.g-item-info').append(relatedSimsWidget.el);
    }, this);

    render.call(this);

    return this;
});

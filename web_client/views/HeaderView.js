import HeaderView from 'girder/views/layout/HeaderView';
import { wrap } from 'girder/utilities/PluginUtils';

import LayoutHeaderTemplate from '../templates/layoutHeader.pug';

wrap(HeaderView, 'render', function (render) {
    this.$el.html(LayoutHeaderTemplate());
    this.userView.setElement(this.$('.g-current-user-wrapper')).render();
    this.searchWidget.setElement(this.$('.g-quick-search-container')).render();
});

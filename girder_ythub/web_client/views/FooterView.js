import FooterView from 'girder/views/layout/FooterView';
import { apiRoot } from 'girder/rest';
import { wrap } from 'girder/utilities/PluginUtils';

import LayoutFooterTemplate from '../templates/layoutFooter.pug';
import 'girder/stylesheets/layout/footer.styl';

wrap(FooterView, 'render', function (render) {
    this.$el.html(LayoutFooterTemplate({
        apiRoot: apiRoot
    }));
    return this;
});

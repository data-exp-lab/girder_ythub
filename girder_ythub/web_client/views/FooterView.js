import FooterView from '@girder/core/views/layout/FooterView';
import { apiRoot } from '@girder/core/rest';
import { wrap } from '@girder/core/utilities/PluginUtils';

import LayoutFooterTemplate from '../templates/layoutFooter.pug';
import '@girder/core/stylesheets/layout/footer.styl';

wrap(FooterView, 'render', function (render) {
    this.$el.html(LayoutFooterTemplate({
        apiRoot: apiRoot
    }));
    return this;
});

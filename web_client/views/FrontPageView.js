import FrontPageView from 'girder/views/body/FrontPageView';
import { wrap } from 'girder/utilities/PluginUtils';
import { apiRoot, staticRoot } from 'girder/rest';
import { getCurrentUser } from 'girder/auth';
import versionInfo from 'girder/version';
import FrontPageTemplate from '../templates/frontPage.pug';

wrap(FrontPageView, 'render', function (render) {
    this.$el.html(FrontPageTemplate({
        apiRoot: apiRoot,
        staticRoot: staticRoot,
        currentUser: getCurrentUser(),
        versionInfo: versionInfo
    }));
    return this;
});

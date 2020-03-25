import View from '@girder/core/views/View';
import { restRequest } from '@girder/core/rest';

import template from '../templates/runNotebook.pug';
import '../stylesheets/runNotebook.styl';

var RunNotebookView = View.extend({
    initialize: function (settings) {
        restRequest({
            url: 'frontend/' + settings.frontendId,
            type: 'GET'
        }).then((resp) => {
            var frontendId = settings.frontendId;
            var folderId = settings.folderId;
            var scripts = JSON.stringify(settings.scripts || []);
            restRequest({
                url: 'notebook',
                method: 'POST',
                data: {
                    frontendId: frontendId,
                    folderId: folderId,
                    scripts: scripts
                },
                error: null
            }).done((resp) => {
                window.location.assign(resp['url']);
            }).fail((resp) => {
                this.$('.g-validation-failed-message').text('Error: ' + resp.responseJSON.message);
            });
            return resp;
        });
        this.render();
    },

    render: function () {
        this.$el.html(template());
        return this;
    }
});

export default RunNotebookView;

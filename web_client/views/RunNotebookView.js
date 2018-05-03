import View from 'girder/views/View';
import { restRequest } from 'girder/rest';

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
            restRequest({
                url: 'notebook',
                method: 'POST',
                data: {
                    frontendId: frontendId,
                    folderId: folderId
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

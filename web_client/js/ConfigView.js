/**
 * Administrative configuration view.
 */
girder.views.ythub_ConfigView = girder.View.extend({
    events: {
        'submit #g-ythub-config-form': function (event) {
            event.preventDefault();
            this.$('#g-ythub-error-message').empty();

            this._saveSettings([{
                key: 'ythub.tmpnb_url',
                value: this.$('#ythub_tmpnb').val().trim()
            }, {
                key: 'ythub.culling_period',
                value: this.$('#ythub_culling').val().trim()
            }]);
        }
    },
    initialize: function () {
        girder.restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify([
                    'ythub.tmpnb_url',
                    'ythub.culling_period'
                ])
            }
        }).done(_.bind(function (resp) {
            this.render();
            this.$('#ythub_tmpnb').val(resp['ythub.tmpnb_url']);
            this.$('#ythub_culling').val(resp['ythub.culling_period']);
        }, this));
    },

    render: function () {
        this.$el.html(girder.templates.ythub_config());

        if (!this.breadcrumb) {
            this.breadcrumb = new girder.views.PluginConfigBreadcrumbWidget({
                pluginName: 'ytHub',
                el: this.$('.g-config-breadcrumb-container'),
                parentView: this
            }).render();
        }

        return this;
    },

    _saveSettings: function (settings) {
        girder.restRequest({
            type: 'PUT',
            path: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(_.bind(function (resp) {
            girder.events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }, this)).error(_.bind(function (resp) {
            this.$('#g-ythub-error-message').text(
                resp.responseJSON.message);
        }, this));
    }
});

girder.router.route('plugins/ythub/config', 'ythubConfig', function () {
    girder.events.trigger('g:navigateTo', girder.views.ythub_ConfigView);
});

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
            }, {
                key: 'ythub.priv_key',
                value: this.$('#ythub_priv_key').val()
            }, {
                key: 'ythub.pub_key',
                value: this.$('#ythub_pub_key').val()
            }]);
        },
        'click .g-generate-key': function (event) {
            event.preventDefault();
            girder.restRequest({
               type: 'POST',
               path: 'ythub/genkey',
               data: {}
            }).done(_.bind(function (resp) {
               this.$('#ythub_priv_key').val(resp['ythub.priv_key']);
               this.$('#ythub_pub_key').val(resp['ythub.pub_key']);
            }, this));
        }
    },
    initialize: function () {
        girder.restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify([
                    'ythub.tmpnb_url',
                    'ythub.culling_period',
                    'ythub.priv_key',
                    'ythub.pub_key'
                ])
            }
        }).done(_.bind(function (resp) {
            this.render();
            this.$('#ythub_tmpnb').val(resp['ythub.tmpnb_url']);
            this.$('#ythub_culling').val(resp['ythub.culling_period']);
            this.$('#ythub_priv_key').val(resp['ythub.priv_key']);
            this.$('#ythub_pub_key').val(resp['ythub.pub_key']);
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

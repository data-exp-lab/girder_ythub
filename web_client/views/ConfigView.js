import _ from 'underscore';

import PluginConfigBreadcrumbWidget from 'girder/views/widgets/PluginConfigBreadcrumbWidget';
import View from 'girder/views/View';
import events from 'girder/events';
import { restRequest } from 'girder/rest';

import ConfigViewTemplate from '../templates/configView.pug';
import '../stylesheets/configView.styl';

var ConfigView = View.extend({
    events: {
        'submit #g-wholetale-config-form': function (event) {
            event.preventDefault();
            this.$('#g-wholetale-error-message').empty();

            this._saveSettings([{
                key: 'wholetale.tmpnb_url',
                value: this.$('#wholetale_tmpnb').val().trim()
            }, {
                key: 'wholetale.culling_period',
                value: this.$('#wholetale_culling').val().trim()
            }, {
                key: 'wholetale.priv_key',
                value: this.$('#wholetale_priv_key').val()
            }, {
                key: 'wholetale.pub_key',
                value: this.$('#wholetale_pub_key').val()
            }]);
        },
        'click .g-generate-key': function (event) {
            event.preventDefault();
            restRequest({
               type: 'POST',
               path: 'wholetale/genkey',
               data: {}
            }).done(_.bind(function (resp) {
               this.$('#wholetale_priv_key').val(resp['wholetale.priv_key']);
               this.$('#wholetale_pub_key').val(resp['wholetale.pub_key']);
            }, this));
        }
    },
    initialize: function () {
        restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify([
                    'wholetale.tmpnb_url',
                    'wholetale.culling_period',
                    'wholetale.priv_key',
                    'wholetale.pub_key'
                ])
            }
        }).done(_.bind(function (resp) {
            this.render();
            this.$('#wholetale_tmpnb').val(resp['wholetale.tmpnb_url']);
            this.$('#wholetale_culling').val(resp['wholetale.culling_period']);
            this.$('#wholetale_priv_key').val(resp['wholetale.priv_key']);
            this.$('#wholetale_pub_key').val(resp['wholetale.pub_key']);
        }, this));
    },

    render: function () {
        this.$el.html(ConfigViewTemplate());

        if (!this.breadcrumb) {
            this.breadcrumb = new PluginConfigBreadcrumbWidget({
                pluginName: 'WholeTale',
                el: this.$('.g-config-breadcrumb-container'),
                parentView: this
            }).render();
        }

        return this;
    },

    _saveSettings: function (settings) {
        restRequest({
            type: 'PUT',
            path: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(_.bind(function (resp) {
            events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }, this)).error(_.bind(function (resp) {
            this.$('#g-wholetale-error-message').text(
                resp.responseJSON.message);
        }, this));
    }
});

export default ConfigView;

import _ from 'underscore';

import PluginConfigBreadcrumbWidget from '@girder/core/views/widgets/PluginConfigBreadcrumbWidget';
import View from '@girder/core/views/View';
import events from '@girder/core/events';
import { restRequest } from '@girder/core/rest';

import ConfigViewTemplate from '../templates/configView.pug';
import '../stylesheets/configView.styl';

var SETTING_KEYS = [
    'ythub.tmpnb_internal_url',
    'ythub.tmpnb_redirect_url',
    'ythub.culling_period',
    'ythub.culling_frequency',
    'ythub.priv_key',
    'ythub.pub_key'
];

var ConfigView = View.extend({

    events: {
        'submit #g-ythub-config-form': function (event) {
            event.preventDefault();
            this.$('#g-ythub-error-message').empty();

            var settingsList = SETTING_KEYS.map(function (key) {
                let value = this.$(this.settingControlId(key)).val();
                if (typeof value !== 'undefined' && !/key/.test(key)) {
                    value = value.trim();
                }
                return {
                    key: key,
                    value: value
                };
            }, this);

            this._saveSettings(settingsList);
        },
        'click .g-generate-key': function (event) {
            event.preventDefault();
            restRequest({
                type: 'POST',
                url: 'ythub/genkey',
                data: {}
            }).done(_.bind(function (resp) {
                this.$('#ythub-priv-key').val(resp['ythub.priv_key']);
                this.$('#ythub-pub-key').val(resp['ythub.pub_key']);
            }, this));
        }
    },

    initialize: function () {
        restRequest({
            type: 'GET',
            url: 'system/setting',
            data: {
                list: JSON.stringify(SETTING_KEYS)
            }
        }).done(_.bind(function (resp) {
            this.settingVals = resp;
            this.render();
        }, this));
    },

    render: function () {
        this.$el.html(ConfigViewTemplate());

        if (!this.breadcrumb) {
            this.breadcrumb = new PluginConfigBreadcrumbWidget({
                pluginName: 'ytHub',
                el: this.$('.g-config-breadcrumb-container'),
                parentView: this
            }).render();
        }

        if (this.settingVals) {
            for (var i in SETTING_KEYS) {
                var key = SETTING_KEYS[i];
                this.$(this.settingControlId(key)).val(this.settingVals[key]);
            }
        }

        return this;
    },

    settingControlId: function (key) {
        return '#' + key.replace(/(_|\.)/g, '-');
    },

    _saveSettings: function (settings) {
        restRequest({
            type: 'PUT',
            url: 'system/setting',
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
            this.$('#g-ythub-error-message').text(
                resp.responseJSON.message);
        }, this));
    }
});

export default ConfigView;

import $ from 'jquery';
import _ from 'underscore';

import View from '@girder/core/views/View';
import BrowserWidget from '@girder/core/views/widgets/BrowserWidget';
import { getCurrentUser } from '@girder/core/auth';

import ScriptAddWidgetTemplate from '../../templates/widgets/scriptAddWidget.pug';
import '../../stylesheets/scriptAddWidget.styl';

var lastParent = null;

var ScriptAddWidget = View.extend({
    events: {
        'click .g-script-delete-button': 'deleteScript',
        'click .g-open-script-browser': '_openBrowser'
    },

    initialize: function (settings) {
        this.item = settings.item || null;
        this.scriptSelector = new BrowserWidget({
            parentView: this,
            showItems: true,
            selectItem: true,
            root: lastParent || getCurrentUser(),
            titleText: 'Select an item',
            helpText: 'Browse to a directory to select it, then click "Save"',
            input: settings ? {default: settings.input} : false,
            showPreview: true,
            validate: _.noop
        });
        this.listenTo(this.scriptSelector, 'g:saved', function (val) {
            this.$('#g-script-id').val(val.id);
        });
        this.render();
    },

    render: function () {
        this.$el.html(ScriptAddWidgetTemplate({
            item: this.item
        }));
        return this;
    },

    deleteScript: function (e) {
        e.preventDefault();
        $(event.currentTarget).remove();
    },

    _openBrowser: function (e) {
        e.preventDefault();
        this.scriptSelector.setElement($('#g-dialog-container')).render();
    }
});

export default ScriptAddWidget;

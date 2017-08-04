import $ from 'jquery';
import _ from 'underscore';

import router from 'girder/router';
import ItemModel from 'girder/models/ItemModel';
import MarkdownWidget from 'girder/views/widgets/MarkdownWidget';
import BrowserWidget from 'girder/views/widgets/BrowserWidget';
import View from 'girder/views/View';
import { getCurrentUser } from 'girder/auth';
import { restRequest } from 'girder/rest';

import CreateRaftViewTemplate from '../../templates/body/createRaftView.pug';
import ScriptAddWidgetTemplate from '../../templates/widgets/scriptAddWidget.pug';
import FrontendCollection from '../../collections/FrontendCollection';

import 'girder/utilities/jquery/girderEnable';
import 'girder/utilities/jquery/girderModal';

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
            input: false,
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

var CreateRaftView = View.extend({
    events: {
        'submit #g-item-edit-form': function () {
            var scripts = [];
            scripts.forEach.call(document.getElementsByClassName('g-script'), function (el) {
                scripts.push(el.value);
            });
            var fields = {
                name: this.$('#g-name').val(),
                description: this.descriptionEditor.val(),
                metadata: JSON.stringify({
                    raftSpec: {
                        data: this.$('#g-folder-data-id').val(),
                        frontend: this.$('button.g-raft-frontend-select:first-child').val(),
                        scripts: scripts
                    },
                    isRaft: true
                })
            };

            if (this.item) {
                this.updateItem(fields);
            } else {
                this.createRaft(fields);
            }

            this.descriptionEditor.saveText();
            this.$('button.g-save-item').girderEnable(false);
            this.$('.g-validation-failed-message').empty();

            return false;
        },
        'click .g-open-browser': '_openBrowser',
        'click a.g-frontend': function (e) {
            var frontendName = $(e.currentTarget).text();
            var cid = $(e.currentTarget).attr('frontend-cid');
            var frontendId = this.frontends.get(cid).id;
            $('button.g-raft-frontend-select:first-child').text(frontendName);
            $('button.g-raft-frontend-select:first-child').val(frontendId);
        },
        'click button.g-script-add-button': function (e) {
            e.preventDefault();
            this.addNewScript(e);
        }
    },

    initialize: function (settings) {
        this.frontends = new FrontendCollection();
        this.frontends.on('g:changed', function () {
            this.render();
        }, this).fetch();

        this.item = settings.item || null;
        this.parentModel = settings.parentModel;
        this.descriptionEditor = new MarkdownWidget({
            text: this.item ? this.item.get('description') : '',
            prefix: 'item-description',
            placeholder: 'Enter a description',
            enableUploads: false,
            parentView: this
        });
        this.dataSelector = new BrowserWidget({
            parentView: this,
            showItems: false,
            selectItem: false,
            root: lastParent || getCurrentUser(),
            titleText: 'Select a folder with data',
            helpText: 'Browse to a directory to select it, then click "Save"',
            input: false,
            showPreview: true,
            validate: _.noop
        });
        this.listenTo(this.dataSelector, 'g:saved', function (val) {
            this.$('#g-folder-data-id').val(val.id);
        });
        this.render();
    },

    addNewScript: function (event) {
        var newRow = $('<div>').attr({
            class: 'g-script-row'
        }).appendTo(this.$el.find('.g-scripts-container'));

        new ScriptAddWidget({
            el: newRow,
            item: this.item,
            parentView: this
        }).render();
    },

    render: function () {
        this.$el.html(CreateRaftViewTemplate({
            item: this.item,
            frontends: this.frontends.toArray()
        }));
        this.descriptionEditor.setElement(this.$('.g-description-editor-container')).render();

        return this;
    },

    _openBrowser: function () {
        this.dataSelector.setElement($('#g-dialog-container')).render();
    },

    createRaft: function (fields) {
        var item = new ItemModel();

        var params = {
            path: 'folder',
            data: {
                text: 'Public',
                parentType: 'user',
                parentId: getCurrentUser().get('_id')
            }
        };

        const promises = [
            restRequest(params).then((resp) => resp)
        ];

        $.when(...promises).done((folders) => {
            item.set(_.extend(fields, {
                folderId: folders[0]['_id']
            }));
            item.on('g:saved', function () {
                this.trigger('g:saved', item);
            }, this).on('g:error', function (err) {
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
                this.$('button.g-save-item').girderEnable(true);
                this.$('#g-' + err.responseJSON.field).focus();
            }, this).save();
            router.navigate('/rafts', {trigger: true});
        });
    },

    updateItem: function (fields) {
        this.item.set(fields);
        this.item.off().on('g:saved', function () {
            this.$el.modal('hide');
            this.trigger('g:saved', this.item);
        }, this).on('g:error', function (err) {
            this.$('.g-validation-failed-message').text(err.responseJSON.message);
            this.$('button.g-save-item').girderEnable(true);
            this.$('#g-' + err.responseJSON.field).focus();
        }, this).save();
    }
});

export default CreateRaftView;

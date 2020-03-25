import $ from 'jquery';
import _ from 'underscore';

import router from '@girder/core/router';
import ItemModel from '@girder/core/models/ItemModel';
import MarkdownWidget from '@girder/core/views/widgets/MarkdownWidget';
import BrowserWidget from '@girder/core/views/widgets/BrowserWidget';
import View from '@girder/core/views/View';
import { getCurrentUser } from '@girder/core/auth';
import { restRequest } from '@girder/core/rest';

import CreateRaftViewTemplate from '../../templates/body/createRaftView.pug';
import FrontendCollection from '../../collections/FrontendCollection';
import ScriptAddWidget from '../widgets/ScriptAddWidget';
import '../../stylesheets/createRaftView.styl';

import '@girder/core/utilities/jquery/girderEnable';

var lastParent = null;

var CreateRaftView = View.extend({
    events: {
        'submit #g-item-edit-form': function () {
            this.$('.form-group').removeClass('has-error');
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
        },
        'click a.g-cancel-raft': function (e) {
            router.navigate('/rafts', {trigger: true});
        }
    },

    initialize: function (settings) {
        this.frontends = new FrontendCollection();
        this.frontends.on('g:changed', function () {
            this.render();
        }, this).fetch();

        this.item = settings.model || null;
        this.initialValues = settings.initialValues || null;
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
            titleText: this.initialValues ? this.initialValues.data : 'Select a folder with data',
            helpText: 'Browse to a directory to select it, then click "Save"',
            showPreview: true,
            input: this.initialValues ? {default: this.initialValues.data} : false,
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

        if (_.isString(event)) {
            newRow[0].children[0].children[0].value = event;  // Ugly isn't it?
        }
    },

    render: function () {
        this.$el.html(CreateRaftViewTemplate({
            item: this.item,
            frontends: this.frontends.toArray()
        }));
        this.descriptionEditor.setElement(this.$('.g-description-editor-container')).render();

        if (this.item) {
            this.$('#g-name').val(this.item.attributes.name);
        }
        if (this.initialValues) {
            $('button.g-raft-frontend-select:first-child').text(this.initialValues.frontendName);
            $('button.g-raft-frontend-select:first-child').val(this.initialValues.frontendId);
            this.$('#g-folder-data-id').val(this.initialValues.data);
            var parentClass = this;
            this.initialValues.scripts.forEach(function (script) {
                parentClass.addNewScript(script);
            });
        }

        return this;
    },

    _openBrowser: function () {
        this.dataSelector.setElement($('#g-dialog-container')).render();
    },

    createRaft: function (fields) {
        var item = new ItemModel();

        var params = {
            url: 'folder',
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
                router.navigate('/rafts', {trigger: true});
            }, this).on('g:error', function (err) {
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
                this.$('button.g-save-item').girderEnable(true);
                this.$('#g-' + err.responseJSON.field).focus();
            }, this).save();
        });
    },

    updateItem: function (fields) {
        this.item.set(fields);
        this.item.off().on('g:saved', function () {
            this.$el.modal('hide');
            this.trigger('g:saved', this.item);
            router.navigate('/raft/' + this.item.attributes._id + '/run', {trigger: true});
        }, this).on('g:error', function (err) {
            this.$('.g-validation-failed-message').text(err.responseJSON.message);
            this.$('button.g-save-item').girderEnable(true);
            this.$('#g-' + err.responseJSON.field).focus();
        }, this).save();
    }
});

export default CreateRaftView;

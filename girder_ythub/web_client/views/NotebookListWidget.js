import _ from 'underscore';

import PaginateWidget from '@girder/core/views/widgets/PaginateWidget';
import View from '@girder/core/views/View';
import { defineFlags, formatDate, DATE_SECOND } from '@girder/core/misc';
import eventStream from '@girder/core/utilities/EventStream';
import { SORT_DESC } from '@girder/core/constants';
import { restRequest } from '@girder/core/rest';

import NotebookCollection from '../collections/NotebookCollection';
import NotebookListWidgetTemplate from '../templates/NotebookListWidget.pug';
import NotebookStatus from '../NotebookStatus';

import '../stylesheets/notebookListWidget.styl';

var NotebookListWidget = View.extend({
    events: {
        'click .g-notebook-trigger-link': function (e) {
            var cid = $(e.target).attr('cid');
            this.trigger('g:notebookClicked', this.collection.get(cid));
        },

        'click .g-notebook-delete-link': function (e) {
            var url = $(e.currentTarget).attr('notebook-id');
            var widget = this;
            var _delParams = {
                url: 'notebook/' + url,
                type: 'DELETE',
                error: null
            };
            restRequest(_delParams).done(function () {
                widget.trigger('g:changed');
            });
        }
    },

    initialize: function (settings) {
        this.columns = settings.columns || this.columnEnum.COLUMN_ALL;
        this.filter = settings.filter || {};

        this.collection = new NotebookCollection();
        this.collection.sortField = settings.sortField || 'created';
        this.collection.sortDir = settings.sortDir || SORT_DESC;
        this.collection.pageLimit = settings.pageLimit || this.collection.pageLimit;

        this.collection.on('g:changed', function () {
            this.render();
            this.trigger('g:changed');
        }, this).fetch(this.filter);

        this.showHeader = _.has(settings, 'showHeader') ? settings.showHeader : true;
        this.showPaging = _.has(settings, 'showPaging') ? settings.showPaging : true;

        this.paginateWidget = new PaginateWidget({
            collection: this.collection,
            parentView: this
        });
        eventStream.on('g:event.notebook_status', this._statusChange, this);
    },

    columnEnum: defineFlags([
        'COLUMN_STATUS_ICON',
        'COLUMN_NOTEBOOK',
        'COLUMN_FOLDER',
        'COLUMN_CREATED',
        'COLUMN_OWNER',
        'COLUMN_STATUS'
    ], 'COLUMN_ALL'),

    render: function () {
        this.$el.html(NotebookListWidgetTemplate({
            notebooks: this.collection.toArray(),
            showHeader: this.showHeader,
            columns: this.columns,
            columnEnum: this.columnEnum,
            NotebookStatus: NotebookStatus,
            formatDate: formatDate,
            DATE_SECOND: DATE_SECOND
        }));

        if (this.showPaging) {
            this.paginateWidget.setElement(this.$('.g-notebook-pagination')).render();
        }

        return this;
    },

    _statusChange: function (event) {
        var notebook = event.data,
            tr = this.$('tr[notebookId=' + notebook._id + ']');

        if (!tr.length) {
            return;
        }

        if (this.columns & this.columnEnum.COLUMN_STATUS_ICON) {
            tr.find('td.g-status-icon-container').attr('status', notebook.status)
              .find('i').removeClass().addClass(NotebookStatus.icon(notebook.status));
        }
        if (this.columns & this.columnEnum.COLUMN_STATUS) {
            tr.find('td.g-notebook-status-cell').text(NotebookStatus.text(notebook.status));
        }
        if (this.columns & this.columnEnum.COLUMN_CREATED) {
            tr.find('td.g-notebook-created-cell').text(
                formatDate(notebook.created, DATE_SECOND));
        }

        tr.addClass('g-highlight');

        window.setTimeout(function () {
            tr.removeClass('g-highlight');
        }, 1000);
    }
});

export default NotebookListWidget;

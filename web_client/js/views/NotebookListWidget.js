girder.views.ythub_NotebookListWidget = girder.View.extend({
    events: {
        'click .g-notebook-trigger-link': function (e) {
            var cid = $(e.target).attr('cid');
            this.trigger('g:notebookClicked', this.collection.get(cid));
        },

   'click .g-notebook-delete-link': function (e) {
        var url = $(e.currentTarget).attr('notebook-id');
            var widget = this;
            _delParams = {
                path: 'notebook/' + url,
                type: 'DELETE',
                error: null
            };
            girder.restRequest(_delParams).done(function() {
                widget.trigger('g:changed');
            });
        }
    },

    initialize: function (settings) {
        this.columns = settings.columns || this.columnEnum.COLUMN_ALL;
        this.filter = settings.filter || {};

        this.collection = new girder.collections.NotebookCollection();
        this.collection.sortField = settings.sortField || 'created';
        this.collection.sortDir = settings.sortDir || girder.SORT_DESC;
        this.collection.pageLimit = settings.pageLimit || this.collection.pageLimit;

        this.collection.on('g:changed', function () {
            this.render();
            this.trigger('g:changed');
        }, this).fetch(this.filter);

        this.showHeader = _.has(settings, 'showHeader') ? settings.showHeader : true;
        this.showPaging = _.has(settings, 'showPaging') ? settings.showPaging : true;

        this.paginateWidget = new girder.views.PaginateWidget({
            collection: this.collection,
            parentView: this
        });
        girder.eventStream.on('g:event.notebook_status', this._statusChange, this);
    },

    columnEnum: girder.defineFlags([
        'COLUMN_STATUS_ICON',
        'COLUMN_NOTEBOOK',
        'COLUMN_FOLDER',
        'COLUMN_CREATED',
        'COLUMN_OWNER',
        'COLUMN_STATUS'
    ], 'COLUMN_ALL'),

    render: function () {
        var widget = this;

        girder.restRequest({path: 'ythub'}).done(function (resp) {
            widget.$el.html(girder.templates.ythub_notebookList({
                notebooks: widget.collection.toArray(),
                showHeader: widget.showHeader,
                columns: widget.columns,
                hubUrl: resp["url"],
                columnEnum: widget.columnEnum,
                girder: girder
            }));
        });

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
              .find('i').removeClass().addClass(girder.ythub_NotebookStatus.icon(notebook.status));
        }
        if (this.columns & this.columnEnum.COLUMN_STATUS) {
            tr.find('td.g-notebook-status-cell').text(girder.ythub_NotebookStatus.text(notebook.status));
        }
        if (this.columns & this.columnEnum.COLUMN_CREATED) {
            tr.find('td.g-notebook-created-cell').text(
                girder.formatDate(notebook.created, girder.DATE_SECOND));
        }

        tr.addClass('g-highlight');

        window.setTimeout(function () {
            tr.removeClass('g-highlight');
        }, 1000);
    }
});

girder.router.route('notebook/user/:id', 'notebookList', function (id) {
    girder.events.trigger('g:navigateTo', girder.views.ythub_NotebookListWidget, {
        filter: {}
    });
});

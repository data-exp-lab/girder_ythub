girder.wrap(girder.views.HierarchyWidget, 'render', function (render) {
    // Call the underlying render function that we are wrapping
    render.call(this);

    var widget = this;

    _restParams = {
        path: 'notebook',
        type: 'GET',
        data: {
            userId: girder.currentUser.id,
            folderId: widget.parentModel.get('_id')
        },
        error: null
    };
    girder.restRequest(_restParams).done(function (notebooks) {
        if (notebooks.length < 1) {
           $(girder.templates.ythub_folderMenu({
               item: this.model
           })).appendTo(widget.$('.g-folder-actions-menu'));
        } else {
           var notebook = notebooks[0];
           $(girder.templates.ythub_folderMenu_ex({
               goUrl: notebook.url,
               delUrl: notebook._id
           })).appendTo(widget.$('.g-folder-actions-menu'));
        }
    });
});

girder.views.HierarchyWidget.prototype.events['click a.g-visit-notebook'] = function (e) {
    var url = $(e.currentTarget).attr('notebook-id');
    girder.restRequest({path: 'ythub'}).done(function (resp) {
        window.location.replace(resp["url"] + url);
    });
};

girder.views.HierarchyWidget.prototype.events['click a.g-stop-notebook'] = function (e) {
    var url = $(e.currentTarget).attr('notebook-id');
    _delParams = {
        path: 'notebook/' + url,
        type: 'DELETE',
        error: null
    };
    girder.restRequest(_delParams).done();
};

girder.views.HierarchyWidget.prototype.events['click a.g-start-notebook'] = function () {
    var folderId = this.parentModel.id;
    girder.restRequest({path: 'ythub'}).done(function (hub) {
        girder.restRequest({
            path: 'notebook/' + folderId,
            type: 'POST'
        }).done(function (notebook) {
            console.log(notebook);
            window.location.replace(hub["url"] + notebook["url"]);
        });
    });
};

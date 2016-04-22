girder.wrap(girder.views.HierarchyWidget, 'render', function (render) {
    var widget = this;

    if (widget.parentModel.resourceName === 'folder') {
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
            // Call the underlying render function that we are wrapping
            render.call(widget);
            if (notebooks.length < 1) {
                $(girder.templates.ythub_folderMenu({
                    goUrl: '/dev/null',
                    delUrl: '0',
                })).appendTo(widget.$('.g-folder-actions-menu'));
                document.getElementById("go_nb").style.display = "none";
                document.getElementById("stop_nb").style.display = "none";
                document.getElementById("start_nb").style.display = "list-item";
            } else {
                var notebook = notebooks[0];
                $(girder.templates.ythub_folderMenu({
                    goUrl: notebook.url,
                    delUrl: notebook._id
                })).appendTo(widget.$('.g-folder-actions-menu'));
                document.getElementById("go_nb").style.display = "list-item";
                document.getElementById("stop_nb").style.display = "list-item";
                document.getElementById("start_nb").style.display = "none";
            }
        });
    } else {
        render.call(widget);
    }
});

girder.views.HierarchyWidget.prototype.events['click a.g-visit-notebook'] = function (e) {
    var url = $(e.currentTarget).attr('notebook-id');
    girder.restRequest({path: 'ythub'}).done(function (resp) {
        window.location.assign(resp["url"] + url);
    });
};

girder.views.HierarchyWidget.prototype.events['click a.g-stop-notebook'] = function (e) {
    var url = $(e.currentTarget).attr('notebook-id');
    _delParams = {
        path: 'notebook/' + url,
        type: 'DELETE',
        error: null
    };
    girder.restRequest(_delParams).done(function (foo) {
        document.getElementById("go_nb").style.display = "none";
        document.getElementById("stop_nb").style.display = "none";
        document.getElementById("start_nb").style.display = "list-item";
    });
};

girder.views.HierarchyWidget.prototype.events['click a.g-start-notebook'] = function () {
    var folderId = this.parentModel.id;
    girder.restRequest({path: 'ythub'}).done(function (hub) {
        girder.restRequest({
            path: 'notebook/' + folderId,
            type: 'POST'
        }).done(function (notebook) {
            window.location.assign(hub["url"] + notebook["url"]);
        });
    });
};

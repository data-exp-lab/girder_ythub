girder.wrap(girder.views.HierarchyWidget, 'render', function (render) {
    var widget = this;

    if (girder.currentUser && widget.parentModel.resourceName === 'folder') {
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
                $(girder.templates.ytHub_HierarchyWidget({
                    girder: girder,
                })).prependTo(widget.$('.g-folder-header-buttons'));
                document.getElementById("go_nb").style.display = "none";
                document.getElementById("stop_nb").style.display = "none";
                document.getElementById("start_nb").style.display = "list-item";
                document.getElementsByClassName("g-runnb-button")[0].style.display = "inline";
                document.getElementsByClassName("g-gonb-button")[0].style.display = "none";
                document.getElementsByClassName("g-stopnb-button")[0].style.display = "none";
            } else {
                var notebook = notebooks[0];
                $(girder.templates.ythub_folderMenu({
                    goUrl: notebook.url,
                    delUrl: notebook._id
                })).appendTo(widget.$('.g-folder-actions-menu'));
                $(girder.templates.ytHub_HierarchyWidget({
                    girder: girder,
                })).prependTo(widget.$('.g-folder-header-buttons'));
                document.getElementById("go_nb").style.display = "list-item";
                document.getElementById("stop_nb").style.display = "list-item";
                document.getElementById("start_nb").style.display = "none";
                document.getElementsByClassName("g-runnb-button")[0].style.display = "none";
                document.getElementsByClassName("g-gonb-button")[0].style.display = "inline";
                document.getElementsByClassName("g-stopnb-button")[0].style.display = "inline";
            }
        });
    } else {
        render.call(widget);
    }
});

function _visit_nb (e) {
    girder.restRequest({
        path: 'notebook',
        type: 'GET',
        data: {
            folderId: this.parentModel.id,
            userId: girder.currentUser.get('_id'),
        }
    }).done(_.bind(function (resp) {
       var nb_url = resp[0]['containerPath'];
       girder.restRequest({path: 'ythub'}).done(function (resp) {
           window.location.assign(resp["url"] + nb_url);
       });
    }, this));
};

function _stop_nb (e) {
    girder.restRequest({
        path: 'notebook',
        type: 'GET',
        data: {
            folderId: this.parentModel.id,
            userId: girder.currentUser.get('_id'),
        }
    }).done(_.bind(function (resp) {
       var nbId = resp[0]['_id'];
       _delParams = {
           path: 'notebook/' + nbId,
           type: 'DELETE',
           error: null
       };
       girder.restRequest(_delParams).done(function (foo) {
           document.getElementById("go_nb").style.display = "none";
           document.getElementById("stop_nb").style.display = "none";
           document.getElementById("start_nb").style.display = "list-item";
           document.getElementsByClassName("g-runnb-button")[0].style.display = "inline";
           document.getElementsByClassName("g-gonb-button")[0].style.display = "none";
           document.getElementsByClassName("g-stopnb-button")[0].style.display = "none";
       });
    }, this));
};

function _start_nb () {
    var folderId = this.parentModel.id;
    girder.restRequest({path: 'ythub'}).done(function (hub) {
        girder.restRequest({
            path: 'notebook/' + folderId,
            type: 'POST'
        }).done(function (notebook) {
            window.location.assign(hub["url"] + '/' + notebook["containerPath"]);
        });
    });
};

girder.views.HierarchyWidget.prototype.events['click a.g-visit-notebook'] = _visit_nb
girder.views.HierarchyWidget.prototype.events['click a.g-start-notebook'] = _start_nb
girder.views.HierarchyWidget.prototype.events['click a.g-stop-notebook'] = _stop_nb
girder.views.HierarchyWidget.prototype.events['click .g-runnb-button'] = _start_nb
girder.views.HierarchyWidget.prototype.events['click .g-gonb-button'] = _visit_nb
girder.views.HierarchyWidget.prototype.events['click .g-stopnb-button'] = _stop_nb

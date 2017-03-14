import _ from 'underscore';

import HierarchyWidget from 'girder/views/widgets/HierarchyWidget';
import FrontendSelectorWidget from './widgets/FrontendSelectorWidget';
import { restRequest } from 'girder/rest';
import { wrap } from 'girder/utilities/PluginUtils';
import { getCurrentUser } from 'girder/auth';
import ytHubHierarchyWidget from '../templates/ytHubHierarchyWidget.pug';
import ytHubFolderMenu from '../templates/ytHubFolderMenu.pug';


wrap(HierarchyWidget, 'render', function (render) {
    var widget = this;

    if (getCurrentUser() && widget.parentModel.resourceName === 'folder') {
        var _restParams = {
            path: 'notebook',
            type: 'GET',
            data: {
                userId: getCurrentUser().id,
                folderId: widget.parentModel.get('_id')
            },
            error: null
        };
        restRequest(_restParams).done(function (notebooks) {
            // Call the underlying render function that we are wrapping
            render.call(widget);
            if (notebooks.length < 1) {
                $(ytHubFolderMenu({
                    goUrl: '/dev/null',
                    delUrl: '0',
                })).appendTo(widget.$('.g-folder-actions-menu'));
                $(ytHubHierarchyWidget()).prependTo(widget.$('.g-folder-header-buttons'));
                document.getElementById("go_nb").style.display = "none";
                document.getElementById("stop_nb").style.display = "none";
                document.getElementById("start_nb").style.display = "list-item";
                document.getElementsByClassName("g-runnb-button")[0].style.display = "inline";
                document.getElementsByClassName("g-gonb-button")[0].style.display = "none";
                document.getElementsByClassName("g-stopnb-button")[0].style.display = "none";
            } else {
                var notebook = notebooks[0];
                $(ytHubFolderMenu({
                    goUrl: notebook.url,
                    delUrl: notebook._id
                })).appendTo(widget.$('.g-folder-actions-menu'));
                $(ytHubHierarchyWidget()).prependTo(widget.$('.g-folder-header-buttons'));
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
    restRequest({
        path: 'notebook',
        type: 'GET',
        data: {
            folderId: this.parentModel.id,
            userId: getCurrentUser().get('_id'),
        }
    }).done(_.bind(function (resp) {
       var nb_url = resp[0]['containerPath'];
       restRequest({path: 'ythub'}).done(function (resp) {
           window.location.assign(resp["url"] + nb_url);
       });
    }, this));
};

function _stop_nb (e) {
    restRequest({
        path: 'notebook',
        type: 'GET',
        data: {
            folderId: this.parentModel.id,
            userId: getCurrentUser().get('_id'),
        }
    }).done(_.bind(function (resp) {
       var nbId = resp[0]['_id'];
       var _delParams = {
           path: 'notebook/' + nbId,
           type: 'DELETE',
           error: null
       };
       restRequest(_delParams).done(function (foo) {
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
    new FrontendSelectorWidget({
       el: $('#g-dialog-container'),
       parentView: this
    }).render();
};

HierarchyWidget.prototype.events['click a.g-visit-notebook'] = _visit_nb
HierarchyWidget.prototype.events['click a.g-start-notebook'] = _start_nb
HierarchyWidget.prototype.events['click a.g-stop-notebook'] = _stop_nb
HierarchyWidget.prototype.events['click .g-runnb-button'] = _start_nb
HierarchyWidget.prototype.events['click .g-gonb-button'] = _visit_nb
HierarchyWidget.prototype.events['click .g-stopnb-button'] = _stop_nb

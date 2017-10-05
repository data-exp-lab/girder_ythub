import _ from 'underscore';

import HierarchyWidget from 'girder/views/widgets/HierarchyWidget';
import { restRequest } from 'girder/rest';
import { wrap } from 'girder/utilities/PluginUtils';
import { getCurrentUser } from 'girder/auth';

import ytHubHierarchyWidget from '../templates/ytHubHierarchyWidget.pug';
import ytHubFolderMenu from '../templates/ytHubFolderMenu.pug';
import FrontendSelectorWidget from './widgets/FrontendSelectorWidget';

wrap(HierarchyWidget, 'render', function (render) {
    var widget = this;
    render.call(this);
    var hasFolderHeaderButtons = document.getElementsByClassName('g-folder-header-buttons').length > 0;
    var isViewingFolder = widget.parentModel.resourceName === 'folder';

    if (getCurrentUser() && isViewingFolder && hasFolderHeaderButtons) {
        var _restParams = {
            url: 'notebook',
            type: 'GET',
            data: {
                userId: getCurrentUser().id,
                folderId: widget.parentModel.get('_id')
            },
            error: null
        };
        restRequest(_restParams).done(function (notebooks) {
            // Call the underlying render function that we are wrapping
            if (notebooks.length < 1) {
                $(ytHubFolderMenu({
                    goUrl: '/dev/null',
                    delUrl: '0'
                })).appendTo(widget.$('.g-folder-actions-menu'));
                $(ytHubHierarchyWidget()).prependTo(widget.$('.g-folder-header-buttons'));
                document.getElementById('go_nb').style.display = 'none';
                document.getElementById('stop_nb').style.display = 'none';
                document.getElementById('start_nb').style.display = 'list-item';
                document.getElementsByClassName('g-runnb-button')[0].style.display = 'inline';
                document.getElementsByClassName('g-gonb-button')[0].style.display = 'none';
                document.getElementsByClassName('g-stopnb-button')[0].style.display = 'none';
            } else {
                var notebook = notebooks[0];
                $(ytHubFolderMenu({
                    goUrl: notebook.url,
                    delUrl: notebook._id
                })).appendTo(widget.$('.g-folder-actions-menu'));
                $(ytHubHierarchyWidget()).prependTo(widget.$('.g-folder-header-buttons'));
                document.getElementById('go_nb').style.display = 'list-item';
                document.getElementById('stop_nb').style.display = 'list-item';
                document.getElementById('start_nb').style.display = 'none';
                document.getElementsByClassName('g-runnb-button')[0].style.display = 'none';
                document.getElementsByClassName('g-gonb-button')[0].style.display = 'inline';
                document.getElementsByClassName('g-stopnb-button')[0].style.display = 'inline';
            }
        });
    }
});

function _visitNb(e) {
    restRequest({
        url: 'notebook',
        type: 'GET',
        data: {
            folderId: this.parentModel.id,
            userId: getCurrentUser().get('_id')
        }
    }).done(_.bind(function (resp) {
        window.location.assign(resp[0]['url']);
    }, this));
}

function _stopNb(e) {
    restRequest({
        url: 'notebook',
        type: 'GET',
        data: {
            folderId: this.parentModel.id,
            userId: getCurrentUser().get('_id')
        }
    }).done(_.bind(function (resp) {
        var nbId = resp[0]['_id'];
        var _delParams = {
            url: 'notebook/' + nbId,
            type: 'DELETE',
            error: null
        };
        restRequest(_delParams).done(function (foo) {
            document.getElementById('go_nb').style.display = 'none';
            document.getElementById('stop_nb').style.display = 'none';
            document.getElementById('start_nb').style.display = 'list-item';
            document.getElementsByClassName('g-runnb-button')[0].style.display = 'inline';
            document.getElementsByClassName('g-gonb-button')[0].style.display = 'none';
            document.getElementsByClassName('g-stopnb-button')[0].style.display = 'none';
        });
    }, this));
}

function _startNb() {
    // var folderId = this.parentModel.id;
    new FrontendSelectorWidget({
        el: $('#g-dialog-container'),
        parentView: this
    }).render();
}

HierarchyWidget.prototype.events['click a.g-visit-notebook'] = _visitNb;
HierarchyWidget.prototype.events['click a.g-start-notebook'] = _startNb;
HierarchyWidget.prototype.events['click a.g-stop-notebook'] = _stopNb;
HierarchyWidget.prototype.events['click .g-runnb-button'] = _startNb;
HierarchyWidget.prototype.events['click .g-gonb-button'] = _visitNb;
HierarchyWidget.prototype.events['click .g-stopnb-button'] = _stopNb;

girder.models.NotebookModel = girder.AccessControlledModel.extend({
    resourceName: 'notebook'
});

girder.collections.NotebookCollection = girder.Collection.extend({
    resourceName: 'notebook',
    model: girder.models.NotebookModel
});

// The same notebook status enum as the server.
girder.ythub_NotebookStatus = {
    _map: {},

    text: function (status) {
        return this._map[status].text;
    },

    icon: function (status) {
        return this._map[status].icon;
    },

    /**
     * Convert this status text into a value appropriate for an HTML class name.
     */
    classAffix: function (status) {
        return this.text(status).toLowerCase().replace(/ /g, '-');
    },

    /**
     * Add new notebook statuses. The argument should be an object mapping the enum
     * symbol name to an information object for that status. The info object
     * must include a "value" field (its integer value), a "text" field, which
     * is how the status should be rendered as text, and an "icon" field for
     * what classes to apply to the icon for this status.
     */
    registerStatus: function (status) {
        _.each(status, function (info, name) {
            this[name] = info.value;
            this._map[info.value] = {
                text: info.text,
                icon: info.icon
            };
        }, this);
    }
};

girder.ythub_NotebookStatus.registerStatus({
    RUNNING: {
        value: 0,
        text: 'Running',
        icon: 'icon-spin3 animate-spin'
    },
    ERROR: {
        value: 1,
        text: 'Error',
        icon: 'icon-cancel'
    },
});

/**
 * Add an entry to the user dropdown menu to navigate to user's job list view.
 */
girder.wrap(girder.views.LayoutHeaderUserView, 'render', function (render) {
    render.call(this);

    if (girder.currentUser) {
        this.$('#g-user-action-menu>ul').prepend(girder.templates.ythub_userMenu({
            href: '#notebook/user/' + girder.currentUser.id
        }));
    }
    return this;
});

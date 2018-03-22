import _ from 'underscore';

// The same notebook status enum as the server.
var NotebookStatus = {
    _map: {},

    text: function (status) {
        var text = status;
        if (status in this._map) {
            text = this._map[status].text;
        }
        return text;
    },

    icon: function (status) {
        var icon;
        if (status in this._map) {
            icon = this._map[status].icon;
        }
        return icon;
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

NotebookStatus.registerStatus({
    STARTING: {
        value: 0,
        text: 'Starting',
        icon: 'icon-spin3 animate-spin'
    },
    RUNNING: {
        value: 1,
        text: 'Running',
        icon: 'icon-spin3 animate-spin'
    },
    ERROR: {
        value: 2,
        text: 'Error',
        icon: 'icon-cancel'
    }
});

export default NotebookStatus;

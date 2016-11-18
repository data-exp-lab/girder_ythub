#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder import events
from girder.models.notification import ProgressState


API_VERSION = '1.0'


class PluginSettings:
    CULLING_PERIOD = 'ythub.culling_period'
    TMPNB_URL = 'ythub.tmpnb_url'
    HUB_PRIV_KEY = 'ythub.priv_key'
    HUB_PUB_KEY = 'ythub.pub_key'


# Constants representing the setting keys for this plugin
class NotebookStatus(object):
    RUNNING = 0
    ERROR = 1

    @staticmethod
    def isValid(status):
        event = events.trigger('notebook.status.validate', info=status)

        if event.defaultPrevented and len(event.responses):
            return event.responses[-1]

        return status in (NotebookStatus.RUNNING, NotebookStatus.ERROR)

    @staticmethod
    def toNotificationStatus(status):
        if status == NotebookStatus.RUNNING:
            return ProgressState.ACTIVE
        else:
            return ProgressState.ERROR

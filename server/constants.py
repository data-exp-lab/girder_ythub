#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder import events
from girder.models.notification import ProgressState


API_VERSION = '1.1'


class HarvesterType:
    """
    All possible data harverster implementation types.
    """
    DATAONE = 0


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


class ImageStatus(object):
    INVALID = 0
    UNAVAILABLE = 1
    BUILDING = 2
    AVAILABLE = 3

    @staticmethod
    def isValid(status):
        event = events.trigger('ythub.image.status.validate', info=status)

        if event.defaultPrevented and len(event.responses):
            return event.responses[-1]

        return status in (ImageStatus.INVALID, ImageStatus.UNAVAILABLE,
                          ImageStatus.BUILDING, ImageStatus.AVAILABLE)

    @staticmethod
    def toNotificationStatus(status):
        if status in ImageStatus.UNAVAILABLE:
            return ProgressState.QUEUED
        if status == ImageStatus.BUILDING:
            return ProgressState.ACTIVE
        if status == ImageStatus.AVAILABLE:
            return ProgressState.SUCCESS
        else:
            return ProgressState.ERROR

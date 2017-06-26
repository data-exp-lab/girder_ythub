#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder import events


API_VERSION = '2.0'
CATALOG_NAME = 'WholeTale Catalog'


class HarvesterType:
    """
    All possible data harverster implementation types.
    """
    DATAONE = 0


class PluginSettings:
    TMPNB_URL = 'wholetale.tmpnb_url'
    HUB_PRIV_KEY = 'wholetale.priv_key'
    HUB_PUB_KEY = 'wholetale.pub_key'


# Constants representing the setting keys for this plugin
class InstanceStatus(object):
    RUNNING = 0
    ERROR = 1

    @staticmethod
    def isValid(status):
        event = events.trigger('instance.status.validate', info=status)

        if event.defaultPrevented and len(event.responses):
            return event.responses[-1]

        return status in (InstanceStatus.RUNNING, InstanceStatus.ERROR)


class ImageStatus(object):
    INVALID = 0
    UNAVAILABLE = 1
    BUILDING = 2
    AVAILABLE = 3

    @staticmethod
    def isValid(status):
        event = events.trigger('wholetale.image.status.validate', info=status)

        if event.defaultPrevented and len(event.responses):
            return event.responses[-1]

        return status in (ImageStatus.INVALID, ImageStatus.UNAVAILABLE,
                          ImageStatus.BUILDING, ImageStatus.AVAILABLE)

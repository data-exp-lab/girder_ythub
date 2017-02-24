#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder import events
from girder.models.notification import ProgressState


API_VERSION = '2.0'

dataMapSchema = {
    'title': 'dataMap',
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'A schema for a WholeTale Data Map',
    'type': 'object',
    'properties': {
        'dataId': {
            'type': 'string',
            'description': ('An internal unique identifier specific '
                            'to a given repository.'),
        },
        'doi': {
            'type': 'string',
            'description': 'A unique Digital Object Identifier'
        },
        'name': {
            'type': 'string'
        },
        'repository': {
            'type': 'string',
            'description': 'A name of the repository holding the data.'
        },
        'size': {
            'type': 'integer',
            'minimum': 0,
            'description': 'The total size of the dataset in bytes.'
        }
    },
    'required': ['dataId', 'repository']
}

tagsSchema = {
    'title': 'tags',
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'A schema for recipe/image tags',
    'type': 'array',
    'items': {
        'type': 'string'
    }
}

containerConfigSchema = {
    'title': 'containerConfig',
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'A subset of docker runtime configuration used for Tales',
    'type': 'object',
    'properties': {
        'port': {
            'type': 'integer',
        },
        'command': {
            'type': 'string',
        },
        'cpuShares': {
            'type': 'string',
        },
        'memLimit': {
            'type': 'string',
        },
        'user': {
            'type': 'string',
        },
    }
}

containerInfoSchema = {
    'title': 'containerInfo',
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'A subset of docker info parameters used by Tales',
    'type': 'object',
    'properties': {
        'created': {
            'type': 'string',
            'format': 'date-time',
        },
        'containerId': {
            'type': 'string',
        },
        'mountPoint': {
            'type': 'string',
        },
    },
    'required': ['containerId', 'mountPoint'],
}


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
class InstanceStatus(object):
    RUNNING = 0
    ERROR = 1

    @staticmethod
    def isValid(status):
        event = events.trigger('instance.status.validate', info=status)

        if event.defaultPrevented and len(event.responses):
            return event.responses[-1]

        return status in (InstanceStatus.RUNNING, InstanceStatus.ERROR)

    @staticmethod
    def toNotificationStatus(status):
        if status == InstanceStatus.RUNNING:
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder import events
from girder.models.model_base import ValidationException
from .constants import PluginSettings


def validateSettings(event):
    if event.info['key'] == PluginSettings.TMPNB_URL:
        if not event.info['value']:
            raise ValidationException(
                'TmpNB URL must not be empty.', 'value')
        event.preventDefault().stopPropagation()


def load(info):
    events.bind('model.setting.validate', 'ythub', validateSettings)

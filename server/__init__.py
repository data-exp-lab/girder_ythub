#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder import events
from girder.models.model_base import ValidationException
from girder.api.rest import Resource
from girder.api import access
from .constants import PluginSettings


def validateSettings(event):
    if event.info['key'] == PluginSettings.TMPNB_URL:
        if not event.info['value']:
            raise ValidationException(
                'TmpNB URL must not be empty.', 'value')
        event.preventDefault().stopPropagation()


class ytHub(Resource):
    def __init__(self):
        self.resourceName = 'ythub'

        self.route('GET', (), self.get_ythub_url)

    @access.public
    def get_ythub_url(self, params):
        settingModel = self.model('setting')
        return {'url': settingModel.get(PluginSettings.TMPNB_URL)}


def load(info):
    events.bind('model.setting.validate', 'ythub', validateSettings)
    info['apiRoot'].ythub = ytHub()

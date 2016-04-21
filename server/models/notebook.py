#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import requests
import json

from ..constants import PluginSettings
from girder.constants import AccessType, SortDir
from girder.models.model_base import AccessControlledModel


class Notebook(AccessControlledModel):

    def initialize(self):
        self.name = 'notebook'
        compoundSearchIndex = (
            ('userId', SortDir.ASCENDING),
            ('created', SortDir.DESCENDING)
        )

        self.ensureIndices([(compoundSearchIndex, {})])

        self.exposeFields(level=AccessType.WRITE,
                          fields={'created', 'when', 'folderId', '_id',
                                  'userId', 'url'})
        self.exposeFields(level=AccessType.SITE_ADMIN,
                          fields={'args', 'kwargs'})

    def validate(self, notebook):
        return notebook

    def list(self, user=None, folder=None, limit=0, offset=0,
             sort=None, currentUser=None):
        """
        List a page of jobs for a given user.

        :param user: The user who owns the job.
        :type user: dict or None
        :param limit: The page limit.
        :param offset: The page offset
        :param sort: The sort field.
        :param currentUser: User for access filtering.
        """
        cursor_def = {'userId': user['_id'] if user else None}
        if folder is not None:
            cursor_def.update({'folderId': folder['_id']})
        cursor = self.find(cursor_def, sort=sort)

        for r in self.filterResultsByPermission(cursor=cursor,
                                                user=currentUser,
                                                level=AccessType.READ,
                                                limit=limit, offset=offset):
            yield r

    def deleteNotebook(self, notebook, token):
        hub_url = self.model('setting').get(PluginSettings.TMPNB_URL)
        payload = {"girder_token": token['_id'],
                   "collection_id": str(notebook['folderId'])}
        requests.delete(hub_url, json=payload)

    def createNotebook(self, folder, user, token, when=None, save=True):
        existing = self.findOne({
            'folderId': folder['_id'],
            'userId': user['_id'],
        })

        if existing:
            return existing

        now = datetime.datetime.utcnow()
        when = when or now
        hub_url = self.model('setting').get(PluginSettings.TMPNB_URL)

        payload = {"girder_token": token['_id'],
                   "collection_id": str(folder['_id'])}
        r = requests.post(hub_url, json=payload)
        nb = json.loads(r.content.decode('utf8'))

        notebook = {
            'folderId': folder['_id'],
            'userId': user['_id'],
            'url': nb["url"],
            'created': now,
            'when': when,
        }

        self.setPublic(notebook, public=False)
        self.setUserAccess(notebook, user=user, level=AccessType.ADMIN)
        if save:
            notebook = self.save(notebook)

        return notebook

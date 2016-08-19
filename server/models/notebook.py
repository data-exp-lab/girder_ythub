#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import requests
import six

from ..constants import PluginSettings
from girder.api.rest import RestException
from girder.constants import AccessType, SortDir
from girder.models.model_base import \
    AccessControlledModel, ValidationException
from girder.plugins.ythub.constants import NotebookStatus


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
                                  'userId', 'url', 'status',
                                  'containerPath', 'containerId',
                                  'mountPoint', 'lastActivity'})
        self.exposeFields(level=AccessType.SITE_ADMIN,
                          fields={'args', 'kwargs'})

    def validate(self, notebook):
        if not NotebookStatus.isValid(notebook['status']):
            raise ValidationException(
                'Invalid notebook status %s.' % notebook['status'],
                field='status')
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
        cursor_def = {}
        if user is not None:
            cursor_def['userId'] = user['_id']
        if folder is not None:
            cursor_def['folderId'] = folder['_id']
        cursor = self.find(cursor_def, sort=sort)
        for r in self.filterResultsByPermission(cursor=cursor,
                                                user=currentUser,
                                                level=AccessType.READ,
                                                limit=limit, offset=offset):
            yield r

    def deleteNotebook(self, notebook, token):
        payload = {
            'containerId': str(notebook['containerId']),
            'containerPath': str(notebook['containerPath']),
            'mountPoint': str(notebook['mountPoint']),
            'folderId': str(notebook['folderId']),
            'girder_token': str(token['_id']),
        }
        requests.delete(self.model('setting').get(PluginSettings.TMPNB_URL),
                        json=payload)

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
                   "folderId": str(folder['_id'])}

        resp = requests.post(hub_url, json=payload)
        content = resp.content

        if isinstance(content, six.binary_type):
            content = content.decode('utf8')

        try:
            resp.raise_for_status()
        except requests.HTTPError:
            raise RestException(
                'Got %s code from tmpnb, response="%s"/' % (
                    resp.status_code, content
                ), code=502)

        try:
            nb = json.loads(content)
        except ValueError:
            raise RestException('Non-JSON response: %s' % content, code=502)

        notebook = {
            'folderId': folder['_id'],
            'userId': user['_id'],
            'containerId': nb['containerId'],
            'containerPath': nb['containerPath'],
            'mountPoint': nb['mountPoint'],
            'lastActivity': now,
            'status': NotebookStatus.RUNNING,   # be optimistic for now
            'created': now,
            'when': when,
        }

        self.setPublic(notebook, public=False)
        self.setUserAccess(notebook, user=user, level=AccessType.ADMIN)
        if save:
            notebook = self.save(notebook)

        return notebook

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import requests
import six

from girder import events
from ..constants import PluginSettings, API_VERSION, InstanceStatus
from girder.api.rest import RestException
from girder.constants import AccessType, SortDir
from girder.models.model_base import \
    AccessControlledModel, ValidationException


class Instance(AccessControlledModel):

    def initialize(self):
        self.name = 'instance'
        compoundSearchIndex = (
            ('taleId', SortDir.ASCENDING),
            ('creatorId', SortDir.DESCENDING),
            ('name', SortDir.ASCENDING)
        )
        self.ensureIndices([(compoundSearchIndex, {})])

        self.exposeFields(
            level=AccessType.READ,
            fields={'_id', 'created', 'creatorId', 'name', 'taleId'})
        self.exposeFields(
            level=AccessType.WRITE,
            fields={'containerInfo', 'lastActivity', 'status', 'url'})
        events.bind('model.user.save.created', 'wholetale',
                    self._addDefaultFolders)

    def validate(self, instance):
        if not InstanceStatus.isValid(instance['status']):
            raise ValidationException(
                'Invalid instance status %s.' % instance['status'],
                field='status')
        return instance

    def list(self, user=None, tale=None, limit=0, offset=0,
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
            cursor_def['creatorId'] = user['_id']
        if tale is not None:
            cursor_def['taleId'] = tale['_id']
        cursor = self.find(cursor_def, sort=sort)
        for r in self.filterResultsByPermission(
                cursor=cursor, user=currentUser, level=AccessType.READ,
                limit=limit, offset=offset):
            yield r

    def deleteInstance(self, instance, token):
        payload = {
            'instanceId': str(instance['_id']),
            'girder_token': str(token['_id']),
        }
        headers = {'docker-host': str(instance['containerInfo']['host']),
                   'content-type': 'application/json'}
        requests.delete(self.model('setting').get(PluginSettings.TMPNB_URL),
                        json=payload, headers=headers)
        # TODO: handle error
        self.remove(instance)

    def createInstance(self, tale, user, token, name=None, save=True):
        existing = self.findOne({
            'taleId': tale['_id'],
            'userId': user['_id'],
        })
        if existing:
            return existing

        if not name:
            name = tale['name']

        now = datetime.datetime.utcnow()
        hub_url = self.model('setting').get(PluginSettings.TMPNB_URL)
        payload = {'girder_token': str(token['_id']),
                   'taleId': str(tale['_id']),
                   'api_version': API_VERSION}

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
            resp = json.loads(content)
        except ValueError:
            raise RestException('Non-JSON response: %s' % content, code=502)

        instance = {
            'taleId': tale['_id'],
            'created': now,
            'creatorId': user['_id'],
            'lastActivity': now,
            'containerInfo': resp,
            'name': name,
            'status': InstanceStatus.RUNNING,   # be optimistic for now
            'url': resp['containerPath'],
        }

        self.setUserAccess(instance, user=user, level=AccessType.ADMIN)
        if save:
            instance = self.save(instance)

        return instance

    def _addDefaultFolders(self, event):
        user = event.info
        instanceFolder = self.model('folder').createFolder(
            user, 'Instances', parentType='user', public=True, creator=user)
        self.model('folder').setUserAccess(
            instanceFolder, user, AccessType.ADMIN, save=True)

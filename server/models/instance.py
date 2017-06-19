#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from ..constants import API_VERSION, InstanceStatus
from girder.constants import AccessType, SortDir
from girder.models.model_base import \
    AccessControlledModel, ValidationException
from girder.plugins.worker import getCeleryApp, getWorkerApiUrl


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
            'apiUrl': getWorkerApiUrl()
        }

        instanceTask = getCeleryApp().send_task(
            'gwvolman.tasks.shutdown_container', args=[payload],
            queue='manager',
        )
        instanceTask.get()

        volumeTask = getCeleryApp().send_task(
            'gwvolman.tasks.remove_volume', args=[payload],
            queue=instance['containerInfo']['nodeId']
        )
        volumeTask.get()

        # TODO: handle error
        self.remove(instance)

    def createInstance(self, tale, user, token, name=None, save=True):
        existing = self.findOne({
            'taleId': tale['_id'],
            'creatorId': user['_id'],
        })
        if existing:
            return existing

        if not name:
            name = tale['name']

        now = datetime.datetime.utcnow()
        payload = {
            'girder_token': str(token['_id']),
            'apiUrl': getWorkerApiUrl(),
            'taleId': str(tale['_id']),
            'api_version': API_VERSION
        }

        volumeTask = getCeleryApp().send_task(
            'gwvolman.tasks.create_volume', args=[payload]
        )
        volume = volumeTask.get()
        payload.update(volume)

        serviceTask = getCeleryApp().send_task(
            'gwvolman.tasks.launch_container', args=[payload],
            queue='manager'
        )
        service = serviceTask.get()
        service.update(volume)

        instance = {
            'taleId': tale['_id'],
            'created': now,
            'creatorId': user['_id'],
            'lastActivity': now,
            'containerInfo': service,
            'name': name,
            'status': InstanceStatus.RUNNING,   # be optimistic for now
            'url': service['containerPath'],
        }

        self.setUserAccess(instance, user=user, level=AccessType.ADMIN)
        if save:
            instance = self.save(instance)

        return instance

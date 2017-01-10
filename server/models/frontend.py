# -*- coding: utf-8 -*-

import datetime
import re
from girder.models.model_base import \
    AccessControlledModel, ValidationException
from girder.constants import AccessType


class Frontend(AccessControlledModel):

    def initialize(self):
        self.name = 'frontend'
        self.exposeFields(level=AccessType.READ,
                          fields={'_id', 'imageName', 'command', 'memLimit',
                                  'user', 'cpuShares', 'port', 'created',
                                  'updated', 'description', 'public'})

    def validate(self, frontend):
        if not re.match('(?:[a-z]+/)?([a-z]+)(?::[0-9]+)?',
                        frontend['imageName']):
            raise ValidationException(
                'Invalid image name: %s.' % frontend['imageName'],
                field='imageName')
        return frontend

    def createFrontend(self, imageName, memLimit='1024m', command=None,
                       user=None, cpuShares=None, port=None, save=True,
                       description=None, public=None):
        now = datetime.datetime.utcnow()
        frontend = {
            'imageName': imageName,
            'memLimit': memLimit,
            'user': user,
            'cpuShares': cpuShares,
            'port': port,
            'command': command,
            'description': description,
            'public': public,
            'created': now,
            'updated': now
        }
        if public is not None and isinstance(public, bool):
            self.setPublic(frontend, public, save=False)

        if save:
            frontend = self.save(frontend)
        return frontend

    def updateFrontend(self, frontend):
        '''
        Updates a frontend.

        :param frontend: The frontend document to update.
        :type frontend: dict
        :returns: The frontend document that was edited.
        '''
        frontend['updated'] = datetime.datetime.utcnow()
        return self.save(frontend)

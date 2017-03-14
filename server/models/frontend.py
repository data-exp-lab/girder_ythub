# -*- coding: utf-8 -*-

import datetime
import re
from girder.models.model_base import \
    AccessControlledModel, ValidationException
from girder.constants import AccessType

_DOCKER_IMAGENAME = re.compile(
    '^(?:(?=[^:\/]{1,253})(?!-)[a-zA-Z0-9-]{1,63}(?<!-)'
    '(?:\.(?!-)[a-zA-Z0-9-]{1,63}(?<!-))*(?::[0-9]{1,5})?/)?((?![._-])'
    '(?:[a-z0-9._-]*)(?<![._-])(?:/(?![._-])[a-z0-9._-]*(?<![._-]))*)'
    '(?::(?![.-])[a-zA-Z0-9_.-]{1,128})?$')


class Frontend(AccessControlledModel):

    def initialize(self):
        self.name = 'frontend'
        self.exposeFields(level=AccessType.READ,
                          fields={'_id', 'imageName', 'command', 'memLimit',
                                  'user', 'cpuShares', 'port', 'created',
                                  'updated', 'description', 'public'})

    def validate(self, frontend):
        if not _DOCKER_IMAGENAME.match(frontend['imageName']):
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

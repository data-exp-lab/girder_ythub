# -*- coding: utf-8 -*-

import datetime
import re

from girder.models.model_base import \
    AccessControlledModel, ValidationException
from girder.constants import AccessType

from ..constants import ImageStatus


_GIT_REPO_REGEX = re.compile('(\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/*(.*)')
_DEFAULT_ICON = ('https://github.com/whole-tale/dashboard/blob/d1914c9'
                 '/public/images/whole_tale_logo.png')


class Image(AccessControlledModel):

    def initialize(self):
        self.name = 'image'
        self.ensureIndices(
            ('parentId', 'fullName', 'recipeId',
             ([('parentId', 1), ('fullName', 1), ('recipeId', 1)], {}))
        )
        self.ensureTextIndex({
            'name': 10,
            'description': 1
        })
        self.exposeFields(
            level=AccessType.READ,
            fields={'_id', 'config', 'created', 'creatorId', 'description',
                    'digest', 'fullName', 'icon',  'name', 'recipeId',
                    'status', 'updated', 'name', 'parentId', 'public', 'tags'}
        )

    def validate(self, image):
        if image is None:
            raise ValidationException('Bogus validation')
        return image

    def createImage(self, recipe, fullName, name=None, tags=None,
                    creator=None, save=True, parent=None, description=None,
                    public=None, config=None, icon=None):

        # TODO: check for existing image based on fullName

        if creator is None:
            creatorId = None
        else:
            creatorId = creator.get('_id', None)

        if parent is not None:
            parentId = parent['_id']
        else:
            parentId = None

        if name is None:
            name = 'TODO: extract from url'

        if tags is None:
            tags = ['latest']
        else:
            if 'latest' not in tags:
                tags.append('latest')

        now = datetime.datetime.utcnow()
        image = {
            'config': config,
            'created': now,
            'creatorId': creatorId,
            'description': description,
            'fullName': fullName,
            'digest': None,
            'icon': icon or _DEFAULT_ICON,
            'name': name,
            'parentId': parentId,
            'public': public,
            'recipeId': recipe['_id'],
            'status': ImageStatus.UNAVAILABLE,
            'tags': tags,
            'updated': now,
        }

        if public is not None and isinstance(public, bool):
            self.setPublic(image, public, save=False)
        if creator is not None:
            self.setUserAccess(image, user=creator, level=AccessType.ADMIN,
                               save=False)
        if save:
            image = self.save(image)
        return image

    def updateImage(self, image):
        '''
        Updates a image.

        :param image: The image document to update.
        :type image: dict
        :returns: The image document that was edited.
        '''
        image['updated'] = datetime.datetime.utcnow()
        return self.save(image)

    def buildImage(self, image):
        image['status'] = ImageStatus.BUILDING
        return self.save(image)

    def checkImage(self, image):
        image['status'] = ImageStatus.AVAILABLE
        image['digest'] = 'set me'
        return self.save(image)

    def copyImage(self, image, recipe, creator=None):
        try:
            image['tags'].remove('latest')
            image = self.save(image)
        except ValueError:
            pass

        return self.createImage(
            recipe, image['fullName'], name=image['name'],
            tags=['latest'], creator=creator, save=True, parent=image,
            description=image['description'], public=image['public'],
            config=image['config'], icon=image.get('icon', _DEFAULT_ICON))

# -*- coding: utf-8 -*-

import datetime

from bson.objectid import ObjectId

from girder.models.model_base import \
    AccessControlledModel
from girder.constants import AccessType


class Tale(AccessControlledModel):

    def initialize(self):
        self.name = 'tale'
        self.ensureIndices(
            ('folderId', 'name', 'imageId',
             ([('folderId', 1), ('name', 1), ('imageId', 1)], {}))
        )
        self.ensureTextIndex({
            'name': 10,
            'description': 1
        })
        self.exposeFields(level=AccessType.READ,
                          fields={'_id', 'config', 'creatorId', 'folderId',
                                  'created', 'imageId', 'name',
                                  'updated', 'description', 'public'})

    def validate(self, tale):
        return tale

    def setPublished(self, tale, publish, save=False):
        assert isinstance(publish, bool)
        tale['published'] = publish or tale['published']
        if save:
            tale = self.save(tale)
        return tale

    def createTale(self, image, folder, creator=None, save=True, name=None,
                   description=None, public=None, config=None, published=False):
        if creator is None:
            creatorId = None
        else:
            creatorId = creator.get('_id', None)

        if name is None:
            name = '{} with {}'.format(image['fullName'], folder['name'])

        now = datetime.datetime.utcnow()
        tale = {
            'config': config,
            'creatorId': creatorId,
            'description': description,
            'folderId': ObjectId(folder['_id']),
            'created': now,
            'imageId': ObjectId(image['_id']),
            'name': name,
            'public': public,
            'published': published,
            'updated': now
        }
        if public is not None and isinstance(public, bool):
            self.setPublic(tale, public, save=False)

        if save:
            tale = self.save(tale)
        return tale

    def updateTale(self, tale):
        '''
        Updates a tale.

        :param tale: The tale document to update.
        :type tale: dict
        :returns: The tale document that was edited.
        '''
        tale['updated'] = datetime.datetime.utcnow()
        return self.save(tale)

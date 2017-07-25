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
            ('folderId', 'title', 'imageId',
             ([('folderId', 1), ('title', 1), ('imageId', 1)], {}))
        )
        self.ensureTextIndex({
            'title': 10,
            'description': 1
        })
        self.modifiableFields = {
            'title', 'description', 'public', 'config', 'updated', 'authors',
            'category', 'icon', 'illustration'
        }
        self.exposeFields(
            level=AccessType.READ,
            fields=({'_id', 'folderId', 'imageId', 'creatorId', 'created'} |
                    self.modifiableFields))
        self.exposeFields(level=AccessType.ADMIN, fields={'published'})

    def validate(self, tale):
        return tale

    def setPublished(self, tale, publish, save=False):
        assert isinstance(publish, bool)
        tale['published'] = publish or tale['published']
        if save:
            tale = self.save(tale)
        return tale

    def list(self, user=None, folder=None, image=None, limit=0, offset=0,
             sort=None, currentUser=None):
        """
        List a page of jobs for a given user.

        :param user: The user who created the tale.
        :type user: dict or None
        :param folder: The folder that's being used by the tale.
        :type folder: dict or None
        :param image: The Image that's being used by the tale.
        :type image: dict or None
        :param limit: The page limit.
        :param offset: The page offset
        :param sort: The sort field.
        :param currentUser: User for access filtering.
        """
        cursor_def = {}
        if user is not None:
            cursor_def['creatorId'] = user['_id']
        if folder is not None:
            cursor_def['folderId'] = folder['_id']
        if image is not None:
            cursor_def['imageId'] = image['_id']

        cursor = self.find(cursor_def, sort=sort)
        for r in self.filterResultsByPermission(
                cursor=cursor, user=currentUser, level=AccessType.READ,
                limit=limit, offset=offset):
            yield r

    def createTale(self, image, folder, creator=None, save=True, title=None,
                   description=None, public=None, config=None, published=False,
                   authors=None, icon=None, category=None, illustration=None):
        if creator is None:
            creatorId = None
        else:
            creatorId = creator.get('_id', None)

        if title is None:
            title = '{} with {}'.format(image['fullName'], folder['name'])
        # if illustration is None:
            # Get image from SILS

        now = datetime.datetime.utcnow()
        tale = {
            'authors': authors,
            'category': category,
            'config': config,
            'creatorId': creatorId,
            'description': description,
            'folderId': ObjectId(folder['_id']),
            'created': now,
            'icon': icon,
            'imageId': ObjectId(image['_id']),
            'illustration': illustration,
            'title': title,
            'public': public,
            'published': published,
            'updated': now
        }
        if public is not None and isinstance(public, bool):
            self.setPublic(tale, public, save=False)
        if creator is not None:
            self.setUserAccess(tale, user=creator, level=AccessType.ADMIN,
                               save=False)
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

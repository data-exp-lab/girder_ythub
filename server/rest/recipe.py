#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.docs import addModel
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, filtermodel, RestException
from girder.constants import AccessType, SortDir, TokenScope
from ..constants import tagsSchema

recipeModel = {
    'properties': {
        '_id': {
            'type': 'string',
            'description': 'unique identifier'
        },
        'name': {'type': 'string'},
        'lowerName': {'type': 'string', 'description': '"name" attribute in lower case'},
        'description': {'type': 'string'},
        'url': {
            'type': 'string',
            'description': ('a URL of an external vcs repository containing '
                            'all the data required to build an image.')
        },
        'commitId': {
            'type': 'string',
            'description': 'An immutable commit identifier'
        },
        'tags': {
            'type': 'array',
            'items': {'type': 'string'},
            'description': 'A human readable identification of the Recipe.',
            'default': ['latest']
        },
        'parentId': {
            'type': 'string',
            'description': 'ID of a previous version of the Recipe'
        },
        'public': {
            'type': 'boolean',
            'default': True,
            'description': 'If set to true the recipe can be accessed by anyone'
        },
        'created': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The time when the recipe was created.'
        },
        'creatorId': {
            'type': 'string',
            'description': 'A unique identifier of the user that created the recipe.'
        },
        'updated': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The last time when the recipe was modified.'
        },
    },
    'description': 'Object representing data required to build an Image.',
    'required': ['_id', 'name', 'url', 'commitId', 'tags'],
    'example': {
        '_accessLevel': 2,
        '_id': '5873dcdbaec030000144d233',
        '_modelType': 'recipe',
        'commitId': '1234abc',
        'creatorId': '18312dcdbaec030000144d233',
        'created': '2017-01-09T18:56:27.262000+00:00',
        'description': 'My fancy recipe',
        'name': 'Xarthisius/wt_recipe',
        'parentId': 'null',
        'public': True,
        'tags': ['latest', 'py3'],
        'url': 'https://github.com/Xarthisius/wt_recipe',
        'updated': '2017-01-10T16:15:17.313000+00:00',
    },
}
addModel('recipe', recipeModel, resources='recipe')


class Recipe(Resource):

    def __init__(self):
        super(Recipe, self).__init__()
        self.resourceName = 'recipe'

        self.route('GET', (), self.listRecipes)
        self.route('POST', (), self.createRecipe)
        self.route('GET', (':id',), self.getRecipe)
        # self.route('POST', (':id',), self.copyRecipe)
        self.route('PUT', (':id',), self.updateRecipe)
        self.route('DELETE', (':id',), self.deleteRecipe)

    @access.public
    @filtermodel(model='recipe', plugin='ythub')
    @autoDescribeRoute(
        Description(('Returns all recipes from the system '
                    'that user has access to'))
        .responseClass('recipe', array=True)
        .param('parentId', "The ID of the recipe's parent.", required=False)
        .param('text', ('Perform a full text search for recipe with matching '
                        'name or description.'), required=False)
        .param('tag', 'Search all recipes with a given tag.', required=False)
        .pagingParams(defaultSort='lowerName',
                      defaultSortDir=SortDir.DESCENDING)
    )
    def listRecipes(self, parentId, text, tag, limit, offset, sort, params):
        user = self.getCurrentUser()

        if parentId:
            parent = self.model('recipe', 'ythub').load(
                parentId, user=user, level=AccessType.READ, exc=True)

            filters = {}
            if text:
                filters['$text'] = {
                    '$search': text
                }
            if tag:
                print('Do filtering by tag when I figure it out')

            return list(self.model('recipe', 'ythub').childRecipes(
                parent=parent, user=user,
                offset=offset, limit=limit, sort=sort, filters=filters))
        elif text:
            return list(self.model('recipe', 'ythub').textSearch(
                text, user=user, limit=limit, offset=offset, sort=sort))
        elif tag:
            raise RestException('Can filter by tag. yet...')
        else:
            raise RestException('Invalid search mode.')

    @access.public(scope=TokenScope.DATA_READ)
    @filtermodel(model='recipe', plugin='ythub')
    @autoDescribeRoute(
        Description('Get a recipe by ID.')
        .modelParam('id', model='recipe', plugin='ythub', level=AccessType.READ)
        .responseClass('recipe')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the recipe.', 403)
    )
    def getRecipe(self, recipe, params):
        return recipe

    @access.user
    @autoDescribeRoute(
        Description('Update an existing recipe.')
        .modelParam('id', model='recipe', plugin='ythub', level=AccessType.WRITE,
                    description='The ID of the recipe.')
        .param('name', 'A name of the recipe.', required=False)
        .param('description', 'A description of the recipe.',
               required=False)
        .param('public', 'Whether the recipe should be publicly visible.'
               ' Defaults to True.', dataType='boolean', required=False,
               default=True)
        .jsonParam('tags', 'A human readable labels for the recipe.',
                   required=False, schema=tagsSchema)
        .responseClass('recipe')
        .errorResponse('ID was invalid.')
        .errorResponse('Read/write access was denied for the recipe.', 403)
        .errorResponse('Tag already exists.', 409)
    )
    def updateRecipe(self, recipe, name, description, public, tags, params):
        if name is not None:
            recipe['name'] = name
        if description is not None:
            recipe['description'] = description
        if tags is not None:
            recipe['tags'] = tags
        # TODO: tags magic
        self.model('recipe', 'ythub').setPublic(recipe, public)
        return self.model('recipe', 'ythub').updateRecipe(recipe)

    @access.admin
    @autoDescribeRoute(
        Description('Delete an existing recipe.')
        .modelParam('id', model='recipe', plugin='ythub', level=AccessType.WRITE,
                    description='The ID of the recipe.')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the recipe.', 403)
    )
    def deleteRecipe(self, recipe, params):
        self.model('recipe', 'ythub').remove(recipe)

    @access.user
    @filtermodel(model='recipe', plugin='ythub')
    @autoDescribeRoute(
        Description('Create a new recipe.')
        .param('url', 'A URL of an external vcs repository containing '
               'all the data required to build an image.', dataType='string',
               required=True)
        .param('commitId', 'An immutable commit identifier', dataType='string',
               required=True)
        .param('name', 'A name of the recipe.', required=False)
        .param('description', 'A description of the recipe.',
               required=False)
        .param('public', 'Whether the recipe should be publicly visible.'
               ' Defaults to True.', dataType='boolean', required=False)
        .jsonParam('tags', 'A human readable labels for the recipe.',
                   required=False, schema=tagsSchema)
        .responseClass('recipe')
        .errorResponse('Query parameter was invalid')
    )
    def createRecipe(self, url, commitId, name, description, public, tags, params):
        user = self.getCurrentUser()
        return self.model('recipe', 'ythub').createRecipe(
            commitId, url, name=name, tags=tags, creator=user,
            save=True, parent=None, description=description, public=public)

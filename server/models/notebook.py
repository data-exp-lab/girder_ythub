#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from six.moves import urllib
import ssl
import time

from girder import logger
from ..constants import API_VERSION, NotebookStatus
from girder.api.rest import getApiUrl
from girder.constants import AccessType, SortDir
from girder.models.model_base import \
    AccessControlledModel, ValidationException
from girder.plugins.worker import getCeleryApp, getWorkerApiUrl
from tornado.httpclient import HTTPRequest, HTTPError, HTTPClient
# FIXME look into removing tornado


def _wait_for_server(url, timeout=30, wait_time=0.5):
    '''Wait for a server to show up within a newly launched instance.'''
    tic = time.time()
    # Fudge factor of IPython notebook bootup.
    time.sleep(0.5)

    http_client = HTTPClient()
    req = HTTPRequest(url)

    while time.time() - tic < timeout:
        try:
            http_client.fetch(req)
        except HTTPError as http_error:
            code = http_error.code
            logger.info(
                'Booting server at [%s], getting HTTP status [%s]',
                url, code)
            time.sleep(wait_time)
        except ssl.SSLError:
            time.sleep(wait_time)
        else:
            break


class Notebook(AccessControlledModel):

    def initialize(self):
        self.name = 'notebook'
        compoundSearchIndex = (
            ('creatorId', SortDir.ASCENDING),
            ('created', SortDir.DESCENDING)
        )

        self.ensureIndices([(compoundSearchIndex, {})])
        self.exposeFields(level=AccessType.WRITE,
                          fields={'created', 'folderId', '_id',
                                  'creatorId', 'status', 'frontendId',
                                  'serviceInfo', 'url'})
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
            cursor_def['creatorId'] = user['_id']
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
            'serviceInfo': notebook['serviceInfo'],
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
            queue=notebook['serviceInfo']['nodeId']
        )
        volumeTask.get()

        self.remove(notebook)

    def createNotebook(self, folder, user, token, frontend, scripts=None,
                       when=None, save=True):
        existing = self.findOne({
            'folderId': folder['_id'],
            'creatorId': user['_id'],
            'frontendId': frontend['_id']
        })
        if existing:
            return existing

        now = datetime.datetime.utcnow()
        payload = {
            'girder_token': token['_id'],
            'folder': {k: str(v) for k, v in folder.items()},
            'frontend': {k: str(v) for k, v in frontend.items()},
            'scripts': scripts,
            'api_version': API_VERSION
        }

        # do the job
        volumeTask = getCeleryApp().send_task(
            'gwvolman.tasks.create_volume', args=[payload], kwargs={},
        )
        volumeInfo = volumeTask.get()
        payload.update(volumeInfo)

        serviceTask = getCeleryApp().send_task(
            'gwvolman.tasks.launch_container', args=[payload], kwargs={},
            queue='manager'
        )
        serviceInfo = serviceTask.get()
        serviceInfo.update(volumeInfo)

        netloc = urllib.parse.urlsplit(getApiUrl()).netloc
        domain = '{}.{}'.format(
            serviceInfo['serviceId'], netloc.split(':')[0].split('.', 1)[1])
        # FIXME: bring back https
        url = 'http://{}/{}'.format(domain, serviceInfo.get('urlPath', ''))

        # _wait_for_server(url)

        notebook = {
            'folderId': folder['_id'],
            'creatorId': user['_id'],
            'frontendId': frontend['_id'],
            'status': NotebookStatus.RUNNING,   # be optimistic for now
            'created': now,
            'serviceInfo': serviceInfo,
            'url': url
        }

        self.setPublic(notebook, public=False)
        self.setUserAccess(notebook, user=user, level=AccessType.ADMIN)
        if save:
            notebook = self.save(notebook)

        return notebook

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, filtermodel
from girder.constants import AccessType
from girder.models.item import Item


class QMC(Resource):
    """QMC resource."""

    def __init__(self):
        super(QMC, self).__init__()
        self.resourceName = "qmc"

        self.route("GET", (), self.listSimsByConfig)

    @access.public
    @filtermodel(model=Item)
    @autoDescribeRoute(
        Description("List items sharing a common config")
        .responseClass("item", array=True)
        .modelParam(
            "configId",
            "An ID of the item containing the config.",
            required=True,
            model=Item,
            level=AccessType.READ,
            destName="config",
            paramType="query",
        )
        .pagingParams(defaultSort="name")
    )
    def listSimsByConfig(self, config, limit, offset, sort):
        user = self.getCurrentUser()
        _id = str(config["_id"])
        q = {"$or": [{"meta.conf.uuid": _id}, {"meta.conf_file_ids": _id}]}
        return Item().findWithPermissions(
            q, sort=sort, user=user, level=AccessType.READ, limit=limit, offset=offset
        )

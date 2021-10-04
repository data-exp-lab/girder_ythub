#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bson import ObjectId
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
        self.route("GET", ("filter",), self.listQMCByParams)
        self.route("GET", ("count",), self.aggregateQMCByParams)

    @access.public
    @filtermodel(model=Item)
    @autoDescribeRoute(
        Description("List items sharing a common config")
        .responseClass("item", array=True)
        .param(
            "configId", "An UUID of the config file.", required=True, paramType="query"
        )
        .pagingParams(defaultSort="name")
    )
    def listSimsByConfig(self, configId, limit, offset, sort):
        user = self.getCurrentUser()
        result = []
        for meta_key in ("meta.conf.configId", "meta.configFileIds"):
            result += Item().findWithPermissions(
                {meta_key: ObjectId(configId)},
                sort=sort,
                user=user,
                level=AccessType.READ,
                limit=limit,
                offset=offset,
            )
        return result

    @access.public
    @filtermodel(model=Item)
    @autoDescribeRoute(
        Description("List items in range of config parameters")
        .responseClass("item", array=True)
        .param(
            "Tmin",
            "Minimum temperature in K",
            required=False,
            paramType="query",
            default=0,
            dataType="integer",
        )
        .param(
            "Tmax",
            "Maximum temperature in K",
            required=False,
            paramType="query",
            default=10000,
            dataType="integer",
        )
        .param(
            "Pmin",
            "Minimum pressure in GPa",
            required=False,
            paramType="query",
            default=0,
            dataType="integer",
        )
        .param(
            "Pmax",
            "Maximum pressure in GPa",
            required=False,
            paramType="query",
            default=10000,
            dataType="integer",
        )
        .pagingParams(defaultSort="name")
    )
    def listQMCByParams(self, Tmin, Tmax, Pmin, Pmax, limit, offset, sort):
        user = self.getCurrentUser()
        q = {
            "meta.conf.configId": {"$exists": True},
            "meta.conf.tkelvin": {"$gte": Tmin, "$lte": Tmax},
            "meta.conf.pgpa": {"$gte": Pmin, "$lte": Pmax},
        }
        fields = {"meta.qmc": 0}
        return Item().findWithPermissions(
            q,
            sort=sort,
            user=user,
            level=AccessType.READ,
            limit=limit,
            offset=offset,
            fields=fields,
        )

    @access.public
    @autoDescribeRoute(
        Description("Aggregate QMC sims by config parameters (T, P)")
        .param(
            "draw",
            "Magic integer from datatables",
            required=True,
            paramType="query",
            dataType="integer",
        )
        .param(
            "Tmin",
            "Minimum temperature in K",
            required=False,
            paramType="query",
            default=0,
            dataType="integer",
        )
        .param(
            "Tmax",
            "Maximum temperature in K",
            required=False,
            paramType="query",
            default=10000,
            dataType="integer",
        )
        .param(
            "Pmin",
            "Minimum pressure in GPa",
            required=False,
            paramType="query",
            default=0,
            dataType="integer",
        )
        .param(
            "Pmax",
            "Maximum pressure in GPa",
            required=False,
            paramType="query",
            default=10000,
            dataType="integer",
        )
        .pagingParams(defaultSort="name")
    )
    def aggregateQMCByParams(self, draw, Tmin, Tmax, Pmin, Pmax, limit, offset, sort):
        results = []
        user = self.getCurrentUser()

        def query(Tmin=0, Pmin=0, Tmax=100000, Pmax=100000):
            return {
                "meta.conf.configId": {"$exists": True},
                "meta.conf.tkelvin": {"$gte": Tmin, "$lte": Tmax},
                "meta.conf.pgpa": {"$gte": Pmin, "$lte": Pmax},
            }

        search_kwargs = dict(
            sort=[("name", 1)],
            user=user,
            level=AccessType.READ,
            limit=0,
            offset=0,
            fields={},
        )

        total = Item().findWithPermissions(query(), **search_kwargs).count()
        q = query(Tmin, Pmin, Tmax, Pmax)
        totalFiltered = Item().findWithPermissions(q, **search_kwargs).count()

        if sort[0][0] == "T":
            newsort = [("meta.conf.tkelvin", sort[0][1])]
        elif sort[0][0] == "P":
            newsort = [("meta.conf.pgpa", sort[0][1])]
        else:
            newsort = [("name", sort[0][1])]

        search_kwargs.update(
            {
                "sort": newsort,
                "fields": {"meta.qmc": 0},
                "offset": offset,
                "limit": limit,
            }
        )

        for item in Item().findWithPermissions(q, **search_kwargs):
            conf = item["meta"]["conf"]
            results.append(
                {
                    "name": item["name"],
                    "T": conf["tkelvin"],
                    "P": conf["pgpa"],
                    "DT_RowData": {"itemId": item["_id"], "configId": conf["configId"]},
                    "dft": conf.get("input_dft"),
                    "ens": conf["ens"],
                }
            )

        return {
            "draw": int(draw),
            "recordsTotal": total,
            "recordsFiltered": totalFiltered,
            "data": results,
        }

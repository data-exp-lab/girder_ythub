#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bson import ObjectId
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import (
    Resource,
    filtermodel,
    setResponseHeader,
    setContentDisposition,
)
from girder.constants import AccessType
from girder.models.item import Item
from girder.utility import ziputil


class QMCDescription(Description):
    def physRangeParams(self):
        self.param(
            "Tmin",
            "Minimum temperature in K",
            required=False,
            paramType="query",
            default=0,
            dataType="integer",
        )
        self.param(
            "Tmax",
            "Maximum temperature in K",
            required=False,
            paramType="query",
            default=10000,
            dataType="integer",
        )
        self.param(
            "Pmin",
            "Minimum pressure in GPa",
            required=False,
            paramType="query",
            default=0,
            dataType="integer",
        )
        self.param(
            "Pmax",
            "Maximum pressure in GPa",
            required=False,
            paramType="query",
            default=10000,
            dataType="integer",
        )
        return self


class QMC(Resource):
    """QMC resource."""

    def __init__(self):
        super(QMC, self).__init__()
        self.resourceName = "qmc"

        self.route("GET", (), self.listSimsByConfig)
        self.route("GET", ("filter",), self.listQMCByParams)
        self.route("GET", ("table",), self.aggregateQMCByParams)
        self.route("GET", ("count",), self.countQMC)
        self.route("GET", ("download",), self.downloadQMCByParams)

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
        QMCDescription("List items in range of config parameters")
        .responseClass("item", array=True)
        .physRangeParams()
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
        QMCDescription("Aggregate QMC sims by config parameters (T, P)")
        .param(
            "draw",
            "Magic integer from datatables",
            required=True,
            paramType="query",
            dataType="integer",
        )
        .physRangeParams()
        .pagingParams(defaultSort="name")
    )
    def aggregateQMCByParams(self, draw, Tmin, Tmax, Pmin, Pmax, limit, offset, sort):
        results = []
        user = self.getCurrentUser()

        search_kwargs = dict(
            sort=[("name", 1)],
            user=user,
            level=AccessType.READ,
            limit=0,
            offset=0,
            fields={},
        )

        total = Item().findWithPermissions(self.query(), **search_kwargs).count()
        q = self.query(Tmin, Pmin, Tmax, Pmax)
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
                    "input_dft": conf.get("input_dft"),
                    "ens": conf["ens"],
                    "conf_dft": conf.get("config_dft"),
                    "quantum": conf.get("quantum", False),
                }
            )

        return {
            "draw": int(draw),
            "recordsTotal": total,
            "recordsFiltered": totalFiltered,
            "data": results,
        }

    @staticmethod
    def query(Tmin=0, Pmin=0, Tmax=100000, Pmax=100000):
        return {
            "meta.conf.configId": {"$exists": True},
            "meta.conf.tkelvin": {"$gte": Tmin, "$lte": Tmax},
            "meta.conf.pgpa": {"$gte": Pmin, "$lte": Pmax},
        }

    @access.public
    @autoDescribeRoute(
        QMCDescription("Download QMC sims by config parameters (T, P)")
        .physRangeParams()
        .produces("application/zip")
    )
    def downloadQMCByParams(self, Tmin, Tmax, Pmin, Pmax):
        user = self.getCurrentUser()
        search_kwargs = dict(
            sort=[("name", 1)], user=user, level=AccessType.READ, limit=0, offset=0
        )
        q = self.query(Tmin, Pmin, Tmax, Pmax)
        setResponseHeader("Content-Type", "application/zip")
        setContentDisposition("QMC.zip")

        def stream():
            zipobj = ziputil.ZipGenerator()
            for item in Item().findWithPermissions(q, **search_kwargs):
                print(item["_id"])
                for (path, fobj) in Item().fileList(
                    doc=item, user=user, includeMetadata=False, subpath=True
                ):
                    for data in zipobj.addFile(fobj, path):
                        yield data
            yield zipobj.footer()

        return stream

    @access.public
    @autoDescribeRoute(
        Description("Return a count of QMC simulations aggregated by (T, P)")
    )
    def countQMC(self):
        query = {
            "$match": {
                "meta.conf.configId": {"$exists": True},
                "meta.conf.tkelvin": {"$exists": True},
            }
        }
        aggregation = {
            "$group": {
                "_id": {"tkelvin": "$meta.conf.tkelvin", "pgpa": "$meta.conf.pgpa"},
                "count": {"$sum": "$meta.conf.nconf"},
            }
        }
        return list(Item().collection.aggregate([query, aggregation]))

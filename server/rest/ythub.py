#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cherrypy
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json
import os
import re
from urllib.parse import urlparse, urlunparse, parse_qs
from urllib.request import urlopen
import validators

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, getApiUrl, setResponseHeader
from girder.constants import AccessType
from girder.exceptions import RestException
from girder.models.folder import Folder

from girder.plugins.ythub.constants import PluginSettings


_DOI_REGEX = re.compile(r'(10.\d{4,9}/[-._;()/:A-Z0-9]+)', re.IGNORECASE)
_QUOTES_REGEX = re.compile(r'"(.*)"')
_CNTDISP_REGEX = re.compile(r'filename="(.*)"')


class DataverseImportProvider(object):

    @staticmethod
    def query_dataverse(search_url):
        resp = urlopen(search_url).read()
        data = json.loads(resp.decode('utf-8'))['data']
        if data['count_in_response'] != 1:
            raise ValueError
        item = data['items'][0]
        doi = None
        doi_search = _DOI_REGEX.search(item['dataset_citation'])
        if doi_search is not None:
            doi = "doi:" + doi_search.group()  # TODO: get a proper protocol
        return doi

    @staticmethod
    def parse_dataset(url):
        """Extract title, file, doi from Dataverse resource.

        Handles: {siteURL}/dataset.xhtml?persistentId={persistentId}
        Handles: {siteURL}/api/datasets/{:id}
        """
        if "persistentId" in url.query:
            dataset_url = urlunparse(
                url._replace(path='/api/datasets/:persistentId')
            )
        else:
            dataset_url = urlunparse(url)
        resp = urlopen(dataset_url).read()
        data = json.loads(resp.decode('utf-8'))
        doi = '{protocol}:{authority}/{identifier}'.format(**data['data'])
        return doi

    def parse_file_url(self, url):
        """Extract title, file, doi from Dataverse resource.

        Handles:
            {siteURL}/file.xhtml?persistentId={persistentId}&...
            {siteURL}/api/access/datafile/:persistentId/?persistentId={persistentId}
        """
        qs = parse_qs(url.query)
        try:
            full_doi = qs['persistentId'][0]
        except (KeyError, ValueError):
            # fail here in a meaningful way...
            raise
        return os.path.dirname(full_doi)

    def parse_access_url(self, url):
        """Extract title, file, doi from Dataverse resource.

        Handles: {siteURL}/api/access/datafile/{fileId}
        """
        fileId = os.path.basename(url.path)
        search_url = urlunparse(
            url._replace(path='/api/search', query='q=entityId:' + fileId)
        )
        return self.query_dataverse(search_url)

    @staticmethod
    def dataset_full_url(site, doi):
        return "{scheme}://{netloc}/dataset.xhtml?persistentId={doi}".format(
            scheme=site.scheme, netloc=site.netloc, doi=doi
        )


class ytHub(Resource):
    """Meta resource for yt Hub."""

    def __init__(self):
        super(ytHub, self).__init__()
        self.resourceName = "ythub"

        self.route("GET", (), self.get_ythub_url)
        self.route("GET", (":id", "examples"), self.generateExamples)
        self.route("GET", (":id", "registry"), self.generate_pooch_registry)
        self.route("POST", ("genkey",), self.generateRSAKey)
        self.route("GET", ("dataverse",), self.dataverseExternalTools)

    @access.admin
    @autoDescribeRoute(Description("Generate ythub's RSA key"))
    def generateRSAKey(self, params):
        rsa_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        pubkey_pem = (
            rsa_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf8")
        )
        privkey_pem = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf8")
        self.model("setting").set(PluginSettings.HUB_PUB_KEY, pubkey_pem)
        self.model("setting").set(PluginSettings.HUB_PRIV_KEY, privkey_pem)
        return {
            PluginSettings.HUB_PUB_KEY: pubkey_pem,
            PluginSettings.HUB_PRIV_KEY: privkey_pem,
        }

    @access.public
    @autoDescribeRoute(Description("Return url for tmpnb hub."))
    def get_ythub_url(self, params):
        setting = self.model("setting")
        url = setting.get(PluginSettings.REDIRECT_URL)
        if not url:
            url = setting.get(PluginSettings.TMPNB_URL)
        return {"url": url, "pubkey": setting.get(PluginSettings.HUB_PUB_KEY)}

    @access.public
    @autoDescribeRoute(
        Description("Generate example data page.").modelParam(
            "id", model="folder", level=AccessType.READ
        )
    )
    def generateExamples(self, folder, params):
        def get_code(resource):
            try:
                return resource["meta"]["code"]
            except KeyError:
                return "unknown"

        def sizeof_fmt(num, suffix="B"):
            for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
                if abs(num) < 1024.0:
                    return "%3.1f%s%s" % (num, unit, suffix)
                num /= 1024.0
            return "%.1f%s%s" % (num, "Yi", suffix)

        def download_path(_id, resource):
            return "{}/{}/{}/download".format(getApiUrl(), resource, _id)

        result = {}
        user = self.getCurrentUser()
        frontends = list(
            self.model("folder").childFolders(
                parentType="folder", parent=folder, user=user
            )
        )
        for frontend in frontends:
            ds = list(
                self.model("folder").childFolders(
                    parentType="folder", parent=frontend, user=user
                )
            )

            examples = [
                dict(
                    code=get_code(_),
                    description=_["description"],
                    filename=_["name"],
                    size=sizeof_fmt(_["size"]),
                    url=download_path(_["_id"], "folder"),
                )
                for _ in ds
            ]
            ds = list(self.model("folder").childItems(folder=frontend))
            examples += [
                dict(
                    code=get_code(_),
                    description=_["description"],
                    filename=_["name"],
                    size=sizeof_fmt(_["size"]),
                    url=download_path(_["_id"], "item"),
                )
                for _ in ds
            ]
            result[frontend["name"]] = examples

        return result

    @access.public
    @autoDescribeRoute(
        Description("Generate pooch registry for yt data").modelParam(
            "id", model="folder", level=AccessType.READ
        )
    )
    def generate_pooch_registry(self, folder):
        meta = {}
        result = {}
        download_url = getApiUrl() + "/file/{}/download"
        for path, fobj in Folder().fileList(
            folder,
            user=None,
            path="",
            includeMetadata=True,
            subpath=False,
            mimeFilter=None,
            data=False,
        ):
            if path.endswith("metadata.json"):
                name = os.path.dirname(path).replace(".tar.gz", "").replace(".zip", "")
                meta[name] = json.loads(next(fobj()))
            else:
                name = fobj["name"].replace(".tar.gz", "").replace(".zip", "")
                result[name] = {
                    "url": download_url.format(fobj["_id"]),
                    "hash": "sha512:{}".format(fobj["sha512"]),
                }

        for key in meta.keys():
            result[key].update(meta[key])
        return {k: v for k, v in result.items() if v["type"] == "sample"}

    @access.public
    @autoDescribeRoute(
        Description("Convert external tools request and bounce it to the BinderHub.")
        .param(
            "siteUrl",
            "The URL of the Dataverse installation that hosts the file "
            "with the fileId above",
            required=True,
        )
        .param(
            "fileId",
            "The database ID of a file the user clicks 'Explore' on. "
            "For example, 42. This reserved word is required for file level tools "
            "unless you use {filePid} instead.",
            required=False,
        )
        .param(
            "filePid",
            "The Persistent ID (DOI or Handle) of a file the user clicks 'Explore' on. "
            "For example, doi:10.7910/DVN/TJCLKP/3VSTKY. Note that not all installations "
            "of Dataverse have Persistent IDs (PIDs) enabled at the file level. "
            "This reserved word is required for file level tools unless "
            "you use {fileId} instead.",
            required=False,
        )
        .param(
            "apiToken",
            "The Dataverse API token of the user launching the external "
            "tool, if available. Please note that API tokens should be treated with "
            "the same care as a password. For example, "
            "f3465b0c-f830-4bc7-879f-06c0745a5a5c.",
            required=False,
        )
        .param(
            "datasetId",
            "The database ID of the dataset. For example, 42. This reseved word is "
            "required for dataset level tools unless you use {datasetPid} instead.",
            required=False,
        )
        .param(
            "datasetPid",
            "The Persistent ID (DOI or Handle) of the dataset. "
            "For example, doi:10.7910/DVN/TJCLKP. This reseved word is "
            "required for dataset level tools unless you use {datasetId} instead.",
            required=False,
        )
        .param(
            "datasetVersion",
            "The friendly version number ( or :draft ) of the dataset version "
            "the tool is being launched from. For example, 1.0 or :draft.",
            required=False,
        )
        .param(
            "fullDataset",
            "If True, imports the full dataset that "
            "contains the file defined by fileId.",
            dataType="boolean",
            default=True,
            required=False,
        )
        .notes("apiToken is currently ignored.")
    )
    def dataverseExternalTools(
        self,
        siteUrl,
        fileId,
        filePid,
        apiToken,
        datasetId,
        datasetPid,
        datasetVersion,
        fullDataset,
    ):
        if not validators.url(siteUrl):
            raise RestException("Not a valid URL: siteUrl")

        if all(arg is None for arg in (fileId, filePid, datasetId, datasetPid)):
            raise RestException("No data Id provided")

        provider = DataverseImportProvider()

        site = urlparse(siteUrl)
        if fileId:
            try:
                fileId = int(fileId)
            except (TypeError, ValueError):
                raise RestException("Invalid fileId (should be integer)")

            url = "{scheme}://{netloc}/api/access/datafile/{fileId}".format(
                scheme=site.scheme, netloc=site.netloc, fileId=fileId
            )
            doi = provider.parse_access_url(urlparse(url))
        elif datasetId:
            try:
                datasetId = int(datasetId)
            except (TypeError, ValueError):
                raise RestException("Invalid datasetId (should be integer)")
            url = "{scheme}://{netloc}/api/datasets/{_id}".format(
                scheme=site.scheme, netloc=site.netloc, _id=datasetId
            )
            doi = provider.parse_dataset(urlparse(url))
            url = provider.dataset_full_url(site, doi)
        elif filePid:
            url = "{scheme}://{netloc}/file.xhtml?persistentId={doi}".format(
                scheme=site.scheme, netloc=site.netloc, doi=filePid
            )
            doi = provider.parse_file_url(urlparse(url))
        elif datasetPid:
            url = provider.dataset_full_url(site, datasetPid)
            doi = provider.parse_dataset(urlparse(url))

        binder_url = os.environ.get("BINDER_URL", "https://mybinder.org/v2/dataverse/")
        location = os.path.join(binder_url, doi.rsplit(":")[-1])
        setResponseHeader("Location", location)
        cherrypy.response.status = 303

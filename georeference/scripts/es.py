#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 17.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import os
import traceback
import json
from elasticsearch import Elasticsearch
from georeference.settings import TEMPLATE_PUBLIC_WMS_URL
from georeference.settings import TEMPLATE_PUBLIC_WCS_URL
from georeference.settings import GLOBAL_DOWNLOAD_YEAR_THRESHOLD
from georeference.settings import GLOBAL_PERMALINK_RESOLVER
from georeference.settings import TEMPLATE_TMS_URLS
from georeference.utils.georeference import getImageSize
from georeference.utils.parser import toPublicOAI

LOGGER = logging.getLogger(__name__)

MAPPING = {
    'map_id': { 'type': 'text', 'index': True }, # string id
    'file_name': { 'type': 'keyword', 'index': True }, # df_dk_0010001_5248_1933
    'description': { 'type': 'text', 'index': False }, # "Altenberg. - Umdr.-Ausg., aufgen. 1910, hrsg. 1912, au\u00dfers\u00e4chs. Teil 1919, bericht. 1923, einz. Nachtr. 1933. - 1:25000. - Leipzig, 1939. - 1 Kt."
    'map_scale': { 'type': 'long', 'index': True }, # 25000
    'zoomify_url': { 'type': 'text', 'index': False }, #"http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5248_1933/ImageProperties.xml"
    'map_type': { 'type': 'keyword', 'index': True }, # "M"
    'orginal_url': { 'type': 'text', 'index': False }, #"http://fotothek.slub-dresden.de/fotos/df/dk/0010000/df_dk_0010001_5248_1933.jpg"
    'keywords': { 'type': 'text', 'index': False }, # "Druckgraphik;Lithografie & Umdruck"
    'title_long': { 'type': 'text', 'index': False }, #"Me\u00dftischblatt 119 : Altenberg, 1939"
    'title': { 'type': 'keyword', 'index': True }, # Altenberg
    'permalink': { 'type': 'text', 'index': False }, # "http://digital.slub-dresden.de/id335921620"
    'slub_url': { 'type': 'text', 'index': False }, # "http://digital.slub-dresden.de/id335921620"
    'online_resources': { 'type': 'nested' }, # [{	"url":"http://digital.slub-dresden.de/id335921620", "type":"Permalinkk" }]
    'tms_urls': { 'type': 'text', 'index': False }, #["http://vk2-cdn{s}.slub-dresden.de/tms/mtb/df_dk_0010001_5248_1933"],
    'thumb_url': { 'type': 'text', 'index': False }, #"http://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010001_5248_1933.jpg"
    'geometry': {'type': 'geo_shape' }, # GeoJSON
    'has_georeference': {'type': 'boolean', 'index': True },
    'time_published': {'type': 'date', 'index': True } # "1939-1-1"
}

def _getOnlineResourcePermalink(metadataObj):
    """
    :param metadataObj: Metadata
    :type metadataObj: georeference..models.metadata.Metadata
    :result: A online resource which describes a permalink
    :rtype: dict
    """
    return {
        'url': metadataObj.permalink,
        'type': 'Permalink'
    }


def _getOnlineResourceVK20Permalink(oai):
    """
    :param oai: OAI
    :type oai: str
    :result: A online resource which describes a vk20 permalink
    :rtype: dict
    """
    return {
        'url': GLOBAL_PERMALINK_RESOLVER + oai,
        'type': 'Permalink'
    }

def _getOnlineResourceWMS(originalMapObj):
    """
    :param originalMapObj: Map
    :type originalMapObj: georeference.models.original_maps.Map
    :result: A online resource which describes a wms
    :rtype: dict
    """
    # append WMS
    return {
        'url': '%(link_service)s?SERVICE=WMS&VERSION=2.0.0&REQUEST=GetCapabilities' % ({
            'link_service': TEMPLATE_PUBLIC_WMS_URL % originalMapObj.id,
        }),
        'type': 'WMS'
    }

def _getOnlineResourceWCS(originalMapObj):
    """
    :param originalMapObj: Map
    :type originalMapObj: georeference.models.original_maps.Map
    :result: A online resource which describes a wms
    :rtype: dict
    """
    # append WCS
    return {
        'url': '%(link_service)s?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCapabilities' % ({
            'link_service': TEMPLATE_PUBLIC_WCS_URL % originalMapObj.id,
        }),
        'type': 'WCS'
    }

def _getOnlineResourceWCSForDownload(georefMapObj, coverageTitle, extent):
    """
    :param georefMapObj: Georeference map
    :type georefMapObj: georeference.models.georef_maps.GeorefMap
    :type coverageTitle: Title of the wcs coverage
    :param coverageTitle: str
    :param extent: GeoJSON describing the extent
    :type extent: GeoJSON
    :result: A online resource which describes a wms
    :rtype: dict
    """
    image_size = getImageSize(georefMapObj.getAbsPath())

    # get srid and bbox
    coordinates = extent['coordinates'][0]

    # If no crs is defined within the geojson extent object we expect "EPSG:4326" as srid. This is the default srid
    # for geojson geometires
    srid = extent['crs']['properties']['name'] if 'crs' in extent else "EPSG:4326"
    return {
        'url': '%(link_service)s?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCoverage&CoverageID=%(coverage)s&CRS=%(srid)s&BBOX=%(westBoundLongitude)s,%(southBoundLatitude)s,%(eastBoundLongitude)s,%(northBoundLatitude)s&WIDTH=%(width)s&HEIGHT=%(height)s&FORMAT=GEOTIFF' % ({
            'link_service': TEMPLATE_PUBLIC_WCS_URL % georefMapObj.original_map_id,
            'westBoundLongitude': str(coordinates[0][0]),
            'southBoundLatitude': str(coordinates[0][1]),
            'eastBoundLongitude': str(coordinates[2][0]),
            'northBoundLatitude': str(coordinates[2][1]),
            'srid': srid,
            'width': str(image_size['x']),
            'height': str(image_size['y']),
            'coverage': coverageTitle
        }),
        'type': 'download'
    }


def generateDocument(originalMapObj, metadataObj, georefMapObj=None, logger=LOGGER, geometry=None):
    """ Generates a document which matches the es mapping.

    :param originalMapObj: Original map
    :type originalMapObj: georeference.models.original_maps.OriginalMap
    :param metadataObj: Metadata obj
    :type metadataObj: georeference.models.metadata.Metadata
    :param georefMapObj: Georef map
    :type georefMapObj: georeference.models.original_maps.GeorefMap | None
    :param logger: Logger
    :type logger: logging.Logger
    :param geometry: GeoJSON geometry
    :type geometry: dict
    :result: Document matching the es mapping
    :rtype: dict
    """
    try:
        # Necessary for creating the online ressource
        onlineResources = [_getOnlineResourcePermalink(metadataObj)]

        # We can only create georeference ressources if the absolute path exists
        if georefMapObj != None and os.path.exists(georefMapObj.getAbsPath()):
            onlineResources.append(_getOnlineResourceWMS(originalMapObj))
            if metadataObj.time_of_publication.date().year <= GLOBAL_DOWNLOAD_YEAR_THRESHOLD:
                extent = json.loads(georefMapObj.extent)
                onlineResources.append(_getOnlineResourceWCS(originalMapObj))
                onlineResources.append(_getOnlineResourceWCSForDownload(
                    georefMapObj,
                    originalMapObj.file_name,
                    extent,
                ))

        # Create tms link
        tmsUrls = []
        if georefMapObj != None and os.path.exists(georefMapObj.getAbsPath()):
            for template in TEMPLATE_TMS_URLS:
                tmsUrls.append(
                    template % (str(originalMapObj.map_type).lower() + '/' + originalMapObj.file_name)
                )

        return {
            'map_id': toPublicOAI(originalMapObj.id),
            'file_name': originalMapObj.file_name,
            'description': metadataObj.description,
            'map_scale': int(metadataObj.scale.split(':')[1]),
            'zoomify_url': str(metadataObj.link_zoomify).replace('http:', ''),
            'map_type': originalMapObj.map_type,
            'orginal_url': str(metadataObj.link_jpg).replace('http:', ''),
            'keywords': ';'.join([metadataObj.type,metadataObj.technic]),
            'title_long': metadataObj.title,
            'title': metadataObj.title_short,
            'permalink': metadataObj.permalink,
            'slub_url': metadataObj.permalink,
            'online_resources': onlineResources,
            'tms_urls': tmsUrls,
            'thumb_url': str(metadataObj.link_thumb_small).replace('http:', ''),
            'geometry': geometry if geometry != None else None, #
            'has_georeference': georefMapObj != None,
            'time_published': metadataObj.time_of_publication.date().isoformat()
        }
    except Exception as e:
        logger.error('Failed creating a es document for original map %s.' % originalMapObj.id)
        logger.error(e)
        logger.error(traceback.format_exc())


def getIndex(esConfig, indexName, forceRecreation, logger):
    """ Returns the index. If the index does not create the function creates it.

    :param esConfig: Configuration of the elasticsearch node
    :type esConfig: {{
        host: str,
        port: number,
        username: str|None,
        password: str|None
    }}
    :param indexName: Name of the index
    :type indexName: str
    :param forceRecreation: Signals that the index should be created fresh
    :type forceRecreation: bool
    :param logger: Logger
    :type logger: logging.Logger
    :result: Reference on the index
    :rtype: elasticsearch.Elasticsearch
    """
    try:
        logger.debug('Initialize elasticsearch')
        es = Elasticsearch(
            [{ 'host': esConfig['host'], 'port': esConfig['port']}],
            http_auth=(esConfig['username'],esConfig['password']) if 'username' in esConfig and 'password' in esConfig else None,
            use_ssl=esConfig['ssl'],
            timeout=5000,
        )
        indexExists = es.indices.exists(indexName)

        # Force a reset of the index
        if forceRecreation and indexExists:
            logger.debug('Delete current index, because forceRecreation=True')
            es.indices.delete(indexName, ignore=404)

        # Check if index exists and if not create it
        if indexExists == False or forceRecreation:
            logger.debug('Index "%s" does not exist. Create a fresh index.' % indexName)
            es.indices.create(
                index=indexName,
                body={
                    'mappings': {
                        'properties': MAPPING
                    }
                },
            )
        return es
    except Exception as e:
        logger.error('Failed to get index reference for index %s.' % indexName)
        logger.error(e)
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    getIndex({ 'host': 'localhost', 'port': 9200 }, 'vk20', True, LOGGER)
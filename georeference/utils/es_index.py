#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 17.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os
import traceback
import json
from elasticsearch import Elasticsearch
from georeference.utils.georeference import get_image_size
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id
from georeference.settings import TEMPLATE_PUBLIC_WMS_URL, TEMPLATE_PUBLIC_WCS_URL, GLOBAL_PERMALINK_RESOLVER, \
    TEMPLATE_TMS_URLS

LOGGER = logging.getLogger(__name__)

MAPPING = {
    'map_id': {'type': 'text', 'index': True},  # string id
    'file_name': {'type': 'keyword', 'index': True},  # df_dk_0010001_5248_1933
    'description': {'type': 'text', 'index': False},
    # "Altenberg. - Umdr.-Ausg., aufgen. 1910, hrsg. 1912, au\u00dfers\u00e4chs. Teil 1919, bericht. 1923, einz. Nachtr. 1933. - 1:25000. - Leipzig, 1939. - 1 Kt."
    'map_scale': {'type': 'long', 'index': True},  # 25000
    'zoomify_url': {'type': 'text', 'index': False},
    # "http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5248_1933/ImageProperties.xml"
    'map_type': {'type': 'keyword', 'index': True},  # "M"
    'orginal_url': {'type': 'text', 'index': False},
    # "http://fotothek.slub-dresden.de/fotos/df/dk/0010000/df_dk_0010001_5248_1933.jpg"
    'keywords': {'type': 'text', 'index': False},  # "Druckgraphik;Lithografie & Umdruck"
    'title_long': {'type': 'text', 'index': False},  # "Me\u00dftischblatt 119 : Altenberg, 1939"
    'title': {'type': 'keyword', 'index': True},  # Altenberg
    'permalink': {'type': 'text', 'index': False},  # "http://digital.slub-dresden.de/id335921620"
    'slub_url': {'type': 'text', 'index': False},  # "http://digital.slub-dresden.de/id335921620"
    'online_resources': {'type': 'nested'},
    # [{	"url":"http://digital.slub-dresden.de/id335921620", "type":"Permalinkk" }]
    'tms_urls': {'type': 'text', 'index': False},
    # ["http://vk2-cdn{s}.slub-dresden.de/tms/mtb/df_dk_0010001_5248_1933"],
    'thumb_url': {'type': 'text', 'index': False},
    # "http://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010001_5248_1933.jpg"
    'geometry': {'type': 'geo_shape'},  # GeoJSON
    'has_georeference': {'type': 'boolean', 'index': True},
    'time_published': {'type': 'date', 'index': True},  # "1939-1-1",
    'is_mosaic': {'type': 'boolean', 'index': True} # Signals if the given map is a mosaic map layer
}


def _get_online_resource_permalink(metadata_obj):
    """
    :param metadata_obj: Metadata
    :type metadata_obj: georeference..models.metadata.Metadata
    :result: A online resource which describes a permalink
    :rtype: dict
    """
    return {
        'url': metadata_obj.permalink,
        'type': 'Permalink'
    }


def _get_online_resource_permalink_oai(oai):
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


def _get_online_resource_wms(service_name):
    """
    :param service_name: Name of the service
    :type service_name: str
    :result: A online resource which describes a wms
    :rtype: dict
    """
    # append WMS
    return {
        'url': '%(link_service)s?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities' % ({
            'link_service': TEMPLATE_PUBLIC_WMS_URL.format(service_name),
        }),
        'type': 'WMS'
    }


def _get_online_resource_wcs(raw_map_obj):
    """
    :param raw_map_obj: Map
    :type raw_map_obj: georeference.models.original_maps.Map
    :result: A online resource which describes a wms
    :rtype: dict
    """
    # append WCS
    return {
        'url': '%(link_service)s?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCapabilities' % ({
            'link_service': TEMPLATE_PUBLIC_WCS_URL.format(raw_map_obj.id),
        }),
        'type': 'WCS'
    }


def _get_online_resource_wcs_for_download(georef_map_obj, coverage_title, extent):
    """
    :param georef_map_obj: Georeference map
    :type georef_map_obj: georeference.models.georef_maps.GeorefMap
    :type coverage_title: Title of the wcs coverage
    :param coverage_title: str
    :param extent: GeoJSON describing the extent
    :type extent: GeoJSON
    :result: A online resource which describes a wms
    :rtype: dict
    """
    image_size = get_image_size(georef_map_obj.get_abs_path())

    # get srid and bbox
    coordinates = extent['coordinates'][0]

    # If no crs is defined within the geojson extent object we expect "EPSG:4326" as srid. This is the default srid
    # for geojson geometires
    srid = extent['crs']['properties']['name'] if 'crs' in extent else "EPSG:4326"
    return {
        'url': '%(link_service)s?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCoverage&CoverageID=%(coverage)s&CRS=%(srid)s&BBOX=%(westBoundLongitude)s,%(southBoundLatitude)s,%(eastBoundLongitude)s,%(northBoundLatitude)s&WIDTH=%(width)s&HEIGHT=%(height)s&FORMAT=GEOTIFF' % (
            {
                'link_service': TEMPLATE_PUBLIC_WCS_URL.format(georef_map_obj.raw_map_id),
                'westBoundLongitude': str(coordinates[0][0]),
                'southBoundLatitude': str(coordinates[0][1]),
                'eastBoundLongitude': str(coordinates[2][0]),
                'northBoundLatitude': str(coordinates[2][1]),
                'srid': srid,
                'width': str(image_size['x']),
                'height': str(image_size['y']),
                'coverage': coverage_title
            }),
        'type': 'download'
    }


def generate_es_original_map_document(raw_map_obj, metadata_obj, georef_map_obj=None, logger=LOGGER, geometry=None):
    """ Generates an elasticsearch document for an original_map.

    :param raw_map_obj: Original map
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param metadata_obj: Metadata obj
    :type metadata_obj: georeference.models.metadata.Metadata
    :param georef_map_obj: Georef map
    :type georef_map_obj: georeference.models.original_maps.GeorefMap | None
    :param logger: Logger
    :type logger: logging.Logger
    :param geometry: GeoJSON geometry
    :type geometry: dict
    :result: Document matching the es mapping
    :rtype: dict
    """
    try:
        # Necessary for creating the online ressource
        online_resources = [_get_online_resource_permalink(metadata_obj)]

        # We can only create georeference ressources if the absolute path exists
        if georef_map_obj is not None and os.path.exists(georef_map_obj.get_abs_path()):
            online_resources.append(_get_online_resource_wms(raw_map_obj.id))
            if raw_map_obj.allow_download:
                extent = json.loads(georef_map_obj.extent)
                online_resources.append(_get_online_resource_wcs(raw_map_obj))
                online_resources.append(_get_online_resource_wcs_for_download(
                    georef_map_obj,
                    raw_map_obj.file_name,
                    extent,
                ))

        # Create tms link
        tms_urls = []
        if georef_map_obj is not None and os.path.exists(georef_map_obj.get_abs_path()):
            for template in TEMPLATE_TMS_URLS:
                tms_urls.append(
                    template.format(str(raw_map_obj.map_type).lower() + '/' + raw_map_obj.file_name)
                )

        keywords = ';'.join(list(filter(lambda x: x is not None, [metadata_obj.type, metadata_obj.technic])))

        return {
            'map_id': to_public_map_id(raw_map_obj.id),
            'file_name': raw_map_obj.file_name,
            'description': metadata_obj.description,
            'map_scale': int(raw_map_obj.map_scale) if raw_map_obj.map_scale is not None else None,
            'zoomify_url': str(metadata_obj.link_zoomify).replace('http:', ''),
            'map_type': raw_map_obj.map_type.lower(),
            'keywords': keywords if keywords is not None else '',
            'title_long': metadata_obj.title,
            'title': metadata_obj.title_short,
            'permalink': metadata_obj.permalink,
            'slub_url': metadata_obj.permalink,
            'online_resources': online_resources,
            'tms_urls': tms_urls,
            'thumb_url': str(metadata_obj.link_thumb_small).replace('http:', ''),
            'geometry': geometry if geometry is not None else None,  #
            'has_georeference': georef_map_obj is not None,
            'time_published': metadata_obj.time_of_publication.date().isoformat(),
            'type': 'single_sheet'
        }
    except Exception as e:
        logger.error('Failed creating a es document for georef map %s.' % raw_map_obj.id)
        logger.error(e)
        logger.error(traceback.format_exc())

def generate_es_mosaic_map_document(mosaic_map_obj, logger=LOGGER, geometry=None):
    """ Generates an elasticsearch document for a mosaic_map.

    :param mosaic_map_obj: Mosaic map
    :type mosaic_map_obj: georeference.models.mosaic_maps.MosaicMap
    :param logger: Logger
    :type logger: logging.Logger
    :param geometry: GeoJSON geometry
    :type geometry: dict
    :result: Document matching the es mapping
    :rtype: dict
    """
    try:
        # Necessary for creating the online ressource
        online_resources = [_get_online_resource_wms(mosaic_map_obj.name)]

        return {
            'map_id': to_public_mosaic_map_id(mosaic_map_obj.id),
            'file_name': None,
            'description': mosaic_map_obj.description,
            'map_scale': int(mosaic_map_obj.map_scale) if mosaic_map_obj.map_scale is not None else None,
            'zoomify_url': None,
            'map_type': None,
            'keywords': '',
            'title_long': mosaic_map_obj.title,
            'title': mosaic_map_obj.title_short,
            'permalink': None,
            'slub_url': None,
            'online_resources': online_resources,
            'tms_urls': [],
            'thumb_url': str(mosaic_map_obj.link_thumb).replace('http:', ''),
            'geometry': geometry if geometry is not None else None,  #
            'has_georeference': True,
            'time_published': mosaic_map_obj.time_of_publication.date().isoformat(),
            'type': 'mosaic'
        }
    except Exception as e:
        logger.error('Failed creating a es document for mosaic map %s.' % mosaic_map_obj.id)
        logger.error(e)
        logger.error(traceback.format_exc())


def get_es_index(es_config, index_name, force_recreation, logger):
    """ Returns the index. If the index does not create the function creates it.

    :param es_config: Configuration of the elasticsearch node
    :type es_config: {{
        host: str,
        port: number,
        username: str|None,
        password: str|None
    }}
    :param index_name: Name of the index
    :type index_name: str
    :param force_recreation: Signals that the index should be created fresh
    :type force_recreation: bool
    :param logger: Logger
    :type logger: logging.Logger
    :result: Reference on the index
    :rtype: elasticsearch.Elasticsearch
    """
    try:
        logger.debug('Initialize elasticsearch')
        es = Elasticsearch(
            [{'host': es_config['host'], 'port': es_config['port']}],
            http_auth=(
                es_config['username'],
                es_config['password']) if 'username' in es_config and 'password' in es_config else None,
            use_ssl=es_config['ssl'],
            timeout=5000,
        )
        index_exists = es.indices.exists(index_name)

        # Force a reset of the index
        if force_recreation and index_exists:
            logger.debug('Delete current index, because forceRecreation=True')
            es.indices.delete(index_name, ignore=404)

        # Check if index exists and if not create it
        if index_exists is False or force_recreation:
            logger.debug('Index "%s" does not exist. Create a fresh index.' % index_name)
            es.indices.create(
                index=index_name,
                body={
                    'mappings': {
                        'properties': MAPPING
                    }
                },
            )
        return es
    except Exception as e:
        logger.error('Failed to get index reference for index %s.' % index_name)
        logger.error(e)
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    get_es_index({'host': 'localhost', 'port': 9200}, 'vk20', True, LOGGER)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 06.08.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package


# Created by jacob.mendt@pikobytes.de on 17.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from elasticsearch import Elasticsearch
from loguru import logger

from georeference.config.settings import get_settings
from georeference.config.templates import (
    TEMPLATE_PUBLIC_WMS_URL,
    TEMPLATE_PUBLIC_WCS_URL,
)
from georeference.utils.georeference import get_image_size

MAPPING = {
    "map_id": {"type": "text", "index": True},  # string id
    "file_name": {"type": "keyword", "index": True},  # df_dk_0010001_5248_1933
    "description": {"type": "text", "index": False},
    # "Altenberg. - Umdr.-Ausg., aufgen. 1910, hrsg. 1912, au\u00dfers\u00e4chs. Teil 1919, bericht. 1923, einz. Nachtr. 1933. - 1:25000. - Leipzig, 1939. - 1 Kt."
    "map_scale": {"type": "long", "index": True},  # 25000
    "zoomify_url": {"type": "text", "index": False},
    # "http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5248_1933/ImageProperties.xml"
    "map_type": {"type": "keyword", "index": True},  # "M"
    "keywords": {
        "type": "text",
        "index": False,
    },  # "Druckgraphik;Lithografie & Umdruck"
    "title_long": {
        "type": "text",
        "index": False,
    },  # "Me\u00dftischblatt 119 : Altenberg, 1939"
    "title": {"type": "keyword", "index": True},  # Altenberg
    "permalink": {
        "type": "text",
        "index": False,
    },  # "http://digital.slub-dresden.de/id335921620"
    "slub_url": {
        "type": "text",
        "index": False,
    },  # "http://digital.slub-dresden.de/id335921620"
    "online_resources": {"type": "nested"},
    # [{	"url":"http://digital.slub-dresden.de/id335921620", "type":"Permalinkk" }]
    "tms_urls": {"type": "text", "index": False},
    # ["http://vk2-cdn{s}.slub-dresden.de/tms/mtb/df_dk_0010001_5248_1933"],
    "thumb_url": {"type": "text", "index": False},
    # "http://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010001_5248_1933.jpg"
    "geometry": {"type": "geo_shape"},  # GeoJSON
    "has_georeference": {"type": "boolean", "index": True},
    "time_period_start": {
        "type": "date",
        "index": True,
    },  # "2000-01-01"
    "time_period_end": {
        "type": "date",
        "index": True,
    },  # "2000-12-31"
    "external_content_url": {
        "type": "text",
        "index": False,
    },  # https://ddev.geojson.site/technische_denkmaeler.json
    "external_content_type": {
        "type": "keyword",
        "index": True,
    },  # vkf:geojson-spec-v1, idohist:idohist-v1
    "type": {"type": "keyword", "index": True},  # vector, mosaic, single_sheet
    "time_published": {
        "type": "date",
        "index": True,
    },  # TODO DEPRECATED, remove time_published in next deployment
}


def _get_online_resource_permalink(metadata_obj):
    """
    :param metadata_obj: Metadata
    :type metadata_obj: georeference..models.metadata.Metadata
    :result: A online resource which describes a permalink
    :rtype: dict
    """
    return {"url": metadata_obj.permalink, "type": "Permalink"}


def _get_online_resource_wms(service_name):
    """
    :param service_name: Name of the service
    :type service_name: str
    :result: A online resource which describes a wms
    :rtype: dict
    """
    # append WMS
    return {
        "url": "%(link_service)s?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
        % (
            {
                "link_service": TEMPLATE_PUBLIC_WMS_URL.format(service_name),
            }
        ),
        "type": "WMS",
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
        "url": "%(link_service)s?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCapabilities"
        % (
            {
                "link_service": TEMPLATE_PUBLIC_WCS_URL.format(raw_map_obj.id),
            }
        ),
        "type": "WCS",
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
    coordinates = extent["coordinates"][0]

    # If no crs is defined within the geojson extent object we expect "EPSG:4326" as srid. This is the default srid
    # for geojson geometires
    srid = extent["crs"]["properties"]["name"] if "crs" in extent else "EPSG:4326"
    return {
        "url": "%(link_service)s?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCoverage&CoverageID=%(coverage)s&CRS=%(srid)s&BBOX=%(westBoundLongitude)s,%(southBoundLatitude)s,%(eastBoundLongitude)s,%(northBoundLatitude)s&WIDTH=%(width)s&HEIGHT=%(height)s&FORMAT=GEOTIFF"
        % (
            {
                "link_service": TEMPLATE_PUBLIC_WCS_URL.format(
                    georef_map_obj.raw_map_id
                ),
                "westBoundLongitude": str(coordinates[0][0]),
                "southBoundLatitude": str(coordinates[0][1]),
                "eastBoundLongitude": str(coordinates[2][0]),
                "northBoundLatitude": str(coordinates[2][1]),
                "srid": srid,
                "width": str(image_size["x"]),
                "height": str(image_size["y"]),
                "coverage": coverage_title,
            }
        ),
        "type": "download",
    }


def get_http_auth(es_config):
    if (
        "username" in es_config
        and es_config["username"] is not None
        and "password" in es_config
        and es_config["password"] is not None
    ):
        return (es_config["username"], es_config["password"])
    return None


def get_es_index(es_config, index_name, force_recreation):
    """Returns the index. If the index does not create the function creates it.

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
    :result: Reference on the index
    :rtype: elasticsearch.Elasticsearch
    """

    try:
        es = Elasticsearch(
            [{"host": es_config["host"], "port": es_config["port"]}],
            http_auth=get_http_auth(es_config),
            use_ssl=es_config["ssl"],
            timeout=5000,
        )
        index_exists = es.indices.exists(index_name)

        # Force a reset of the index
        if force_recreation and index_exists:
            logger.debug("Delete current index, because forceRecreation=True")
            es.indices.delete(index_name, ignore=404)

        # Check if index exists and if not create it
        if index_exists is False or force_recreation:
            logger.debug(
                'Index "%s" does not exist. Create a fresh index.' % index_name
            )
            es.indices.create(
                index=index_name,
                body={"mappings": {"properties": MAPPING}},
            )
        return es
    except Exception as e:
        logger.debug(es_config)
        logger.info("Failed to get index reference for index %s." % index_name)
        logger.error(e)


def get_es_index_from_settings(force_recreation: bool):
    settings = get_settings()
    return get_es_index(
        {
            "host": settings.ES_HOST,
            "port": settings.ES_PORT,
            "username": settings.ES_USERNAME,
            "password": settings.ES_PASSWORD,
            "ssl": settings.ES_SSL,
        },
        settings.ES_INDEX_NAME,
        force_recreation,
    )


if __name__ == "__main__":
    get_es_index({"host": "localhost", "port": 9200}, "vk20", True)

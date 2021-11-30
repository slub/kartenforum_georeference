#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Prefix for url routing. This is important if the service run's under an apache server parallel to other
# applications
ROUTE_PREFIX = ''

#
# General
#

# Global error message
GLOBAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'

# Path to gdalwarp tool
GLOBAL_PATH_GDALWARP = 'gdalwarp'

# Path to gdaladdo tool
GLOBAL_PATH_GDALADDO = 'gdaladdo'

# Permalink resolver
GLOBAL_PERMALINK_RESOLVER = 'http://digital.slub-dresden.de/'

# Number of processes used for creating the tms
GLOBAL_TMS_PROCESSES = 2

# Year below which wcs links should be created
GLOBAL_DOWNLOAD_YEAR_THRESHOLD = 1900

#
# ElasticSearch settings
#

# Root of the es instance
ES_ROOT = {
    # 'host': 'localhost',
    # 'port': 9200,
    # 'ssl': False,
    # # 'username': 'username',
    # # 'password': 'password'
    'host': 'search-slub.pikobytes.de',
    'port': 443,
    'ssl': True,
    'username': 'test',
    'password': 'test'

}

# Name of the search index
ES_INDEX_NAME = 'vk20'

#
# Set directory roots
#

# Path to the image root directory
PATH_IMAGE_ROOT = os.path.join(BASE_PATH, '../tmp/org_new')

# Path to the georef root directory
PATH_GEOREF_ROOT = os.path.join(BASE_PATH, '../tmp/geo')

# Path to the tms root directoy
PATH_TMS_ROOT = os.path.join(BASE_PATH, '../tmp/tms')

# Path to the mapfile directory
PATH_MAPFILE_ROOT = os.path.join(BASE_PATH, '../tmp/mapfiles')

# Service tmp
PATH_TMP_ROOT = os.path.join(BASE_PATH, '../tmp/tmp')

# Directory where the mapfiles for the validation process are saved
PATH_TMP_TRANSFORMATION_ROOT = os.path.join(BASE_PATH, '../tmp/tmp')

# The data root is used by the map file an can be defiver from the PATH_TMP_TRANSFORMATION_ROOT. This is
# necessary for proper working with the docker setup
PATH_TMP_TRANSFORMATION_DATA_ROOT = '/mapdata/%s'

# Georeference TMS Cache url
TEMPLATE_TMS_URL = 'http://vk2-cdn{s}.slub-dresden.de/tms2'

#
# Dictonary of supported coordinate reference systems
#

# @TODO check if we can replace this dict through a system wide library
# Definition of used srids
SRC_DICT_WKT = {
    'EPSG:3043':'PROJCS[\"ETRS89 / UTM zone 31N (N-E)\",GEOGCS[\"ETRS89\",DATUM[\"European_Terrestrial_Reference_System_1989\",SPHEROID[\"GRS 1980\",6378137,298.257222101,AUTHORITY[\"EPSG\",\"7019\"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY[\"EPSG\",\"6258\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AUTHORITY[\"EPSG\",\"4258\"]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",0],PARAMETER[\"central_meridian\",3],PARAMETER[\"scale_factor\",0.9996],PARAMETER[\"false_easting\",500000],PARAMETER[\"false_northing\",0],UNIT[\"metre\",1,AUTHORITY[\"EPSG\",\"9001\"]],AUTHORITY[\"EPSG\",\"3043\"]]',
    'EPSG:4314':'GEOGCS[\"DHDN\",DATUM[\"Deutsches_Hauptdreiecksnetz\",SPHEROID[\"Bessel 1841\",6377397.155,299.1528128,AUTHORITY[\"EPSG\",\"7004\"]],TOWGS84[598.1,73.7,418.2,0.202,0.045,-2.455,6.7],AUTHORITY[\"EPSG\",\"6314\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AUTHORITY[\"EPSG\",\"4314\"]]',
    'EPSG:4326':'GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563,AUTHORITY[\"EPSG\",\"7030\"]],AUTHORITY[\"EPSG\",\"6326\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AUTHORITY[\"EPSG\",\"4326\"]]'
}

#
# Configuration parameters for building the WMS and WCS services
#

# Template for the public wms service
TEMPLATE_PUBLIC_WMS_URL = 'https://wms-slub.pikobytes.de/map/%s'

# Template for the public wms service
TEMPLATE_PUBLIC_WCS_URL = 'https://wcs-slub.pikobytes.de/map/%s'

# WMS Service default url template
TEMPLATE_TRANSFORMATION_WMS_URL = 'http://localhost:8080/?map=/etc/mapserver/%s'

# Template for proper building of ids
TEMPLATE_OAI_ID = 'oai:de:slub-dresden:vk:id-%s'

#
# Settings of the daemon. For more information regarding the supported log level see
# https://docs.python.org/3/library/logging.html#levels
#

# Settings for the georeference persistent
DAEMON_SETTINGS = {
    'stdin': os.path.join(BASE_PATH, '../tmp/null'),
    'stdout': os.path.join(BASE_PATH, '../tmp/tty'),
    'stderr': os.path.join(BASE_PATH, '../tmp/tty'),
    'pidfile_path': os.path.join(BASE_PATH, '../tmp/daemon.pid'),
    'pidfile_timeout': 5,
    'sleep_time': 60,
    'wait_on_startup': 15
}

# Settings for logger of the georeference persistent
DAEMON_LOGGER_SETTINGS = {
    'name':'geoereference-daemon',
    'file': os.path.join(BASE_PATH, '../tmp/daemon.log'),
    'level': logging.DEBUG,
    'formatter': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

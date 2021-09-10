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

#
# General
#

# Global error message
GLOBAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'

# Path to the image root directory
PATH_IMAGE_ROOT = os.path.join(BASE_PATH, '../georeference_tests/data_input')

# @TODO check if we can replace this dict through a system wide library
# Definition of used srids
SRC_DICT_WKT = {
    3043:'PROJCS[\"ETRS89 / UTM zone 31N (N-E)\",GEOGCS[\"ETRS89\",DATUM[\"European_Terrestrial_Reference_System_1989\",SPHEROID[\"GRS 1980\",6378137,298.257222101,AUTHORITY[\"EPSG\",\"7019\"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY[\"EPSG\",\"6258\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AUTHORITY[\"EPSG\",\"4258\"]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",0],PARAMETER[\"central_meridian\",3],PARAMETER[\"scale_factor\",0.9996],PARAMETER[\"false_easting\",500000],PARAMETER[\"false_northing\",0],UNIT[\"metre\",1,AUTHORITY[\"EPSG\",\"9001\"]],AUTHORITY[\"EPSG\",\"3043\"]]',
    4314:'GEOGCS[\"DHDN\",DATUM[\"Deutsches_Hauptdreiecksnetz\",SPHEROID[\"Bessel 1841\",6377397.155,299.1528128,AUTHORITY[\"EPSG\",\"7004\"]],TOWGS84[598.1,73.7,418.2,0.202,0.045,-2.455,6.7],AUTHORITY[\"EPSG\",\"6314\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AUTHORITY[\"EPSG\",\"4314\"]]',
    4326:'GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563,AUTHORITY[\"EPSG\",\"7030\"]],AUTHORITY[\"EPSG\",\"6326\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AUTHORITY[\"EPSG\",\"4326\"]]'
}

#
# For the web service
#

# Prefix for url routing. This is important if the service run's under an apache server parallel to other
# applications
ROUTE_PREFIX = ''

# Directory where the mapfiles for the validation process are saved
GEOREFERENCE_VALIDATION_FOLDER = os.path.join(BASE_PATH, '../tmp')

# Service tmp
TMP_DIR = os.path.join(BASE_PATH, '../tmp')

# WMS Service default url template
TEMPLATE_WMS_URL = 'http://localhost:8080/?map=/etc/mapserver/%s'

# WMS data path template
TEMPLATE_WMS_DATA_DIR = '/mapdata/%s'

#
# Parameter for the georeference persistent / persistent georeferencing
#

# @TODO Check if we can replace this through a better configuration injection
# Pattern for building the correct oai id
OAI_ID_PATTERN = 'oai:de:slub-dresden:vk:id-%s'

# Settings for logger of the georeference persistent
GEOREFERENCE_DAEMON_LOGGER = {
    'name':'geoereference-daemon',
    'file': os.path.join(BASE_PATH, '../tmp/'),
    # See supported log level https://docs.python.org/3/library/logging.html#levels
    'level': logging.INFO,
    'formatter': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Settings for the georeference persistent
GEOREFERENCE_DAEMON_SETTINGS = {
    'stdin': os.path.join(BASE_PATH, '../tmp/null'),
    'stdout': os.path.join(BASE_PATH, '../tmp/tty'),
    'stderr': os.path.join(BASE_PATH, '../tmp/tty'),
    'pidfile_path': os.path.join(BASE_PATH, '../tmp/daemon.pid'),
    'pidfile_timeout': 5,
    'sleep_time': 60
}

# Path to gdalwarp tool
GEOREFERENCE_PATH_GDALWARP = 'gdalwarp'

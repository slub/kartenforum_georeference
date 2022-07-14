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

# Permalink resolver
GLOBAL_PERMALINK_RESOLVER = 'http://digital.slub-dresden.de/'

# Number of processes used for creating the tms
GLOBAL_TMS_PROCESSES = 2

#
# ElasticSearch settings
#

# Root of the es instance
ES_ROOT = {
    'host': 'localhost',
    'port': 9200,
    'ssl': False,
    # # 'username': 'username',
    # # 'password': 'password'

}

# Name of the search index
ES_INDEX_NAME = 'vk20'

#
# Set directory roots
#

# Path to the image root directory
PATH_IMAGE_ROOT = os.path.join(BASE_PATH, './__test_data/data_input')

# Path to the georef root directory
PATH_GEOREF_ROOT = os.path.join(BASE_PATH, '../tmp/geo')

# Path to the mosaic root directory
PATH_MOSAIC_ROOT = os.path.join(BASE_PATH, '../tmp/mosaic')

# Path to the tms root directoy
PATH_TMS_ROOT = os.path.join(BASE_PATH, '../tmp/tms')

# Path to the template directory
PATH_MAPFILE_TEMPLATES = os.path.join(BASE_PATH, "./templates")

# Path to the mapfile directory
PATH_MAPFILE_ROOT = os.path.join(BASE_PATH, '../tmp/mapfiles')

# Service tmp
PATH_TMP_ROOT = os.path.join(BASE_PATH, '../tmp/tmp')

# Directory where the mapfiles for the validation process are saved
PATH_TMP_TRANSFORMATION_ROOT = os.path.join(BASE_PATH, '../tmp/tmp')

# The data root is used by the mapfile an can be accessed from the PATH_TMP_TRANSFORMATION_ROOT. This is
# necessary for proper working with the docker setup
PATH_TMP_TRANSFORMATION_DATA_ROOT = '/mapdata/{}'

# Temporary storage for new maps
PATH_TMP_NEW_MAP_ROOT = os.path.join(BASE_PATH, '../tmp/imported_maps')

# Path for the generated thumbnails
PATH_THUMBNAIL_ROOT = os.path.join(BASE_PATH, '../tmp/thumbnails')

# Path to the zoomify files directory
PATH_ZOOMIFY_ROOT = os.path.join(BASE_PATH, '../tmp/zoomify')

#
# GDAL parameters
#

# GDAL_CACHEMAX - This setting can influence the georeference speed. For more information see https://gdal.org/user/configoptions.html
GDAL_CACHEMAX = 1500

# WARP_MEMORY - This setting can influence the georeference speed. For more information see https://gdal.org/programs/gdalwarp.html
GDAL_WARP_MEMORY = 1500

# GDAL_NUM_THREADS - This setting can influence the georeference speed. For more information see https://gdal.org/user/configoptions.html
GDAL_NUM_THREADS = 3

# Georeference TMS Cache url
TEMPLATE_TMS_URLS = [
    'http://vk2-cdn.slub-dresden.de/tms2/{}'
]

#
# Dictonary of supported coordinate reference systems
#

#
# Configuration parameters for building the WMS and WCS services
#

# Template for the public thumbnail images
TEMPLATE_PUBLIC_THUMBNAIL_URL = 'https://thumbnail-slub.pikobytes.de/zoomify/{}'

# Template for the public wms service
TEMPLATE_PUBLIC_WMS_URL = 'https://wms-slub.pikobytes.de/map/{}'

# Template for the public wms service
TEMPLATE_PUBLIC_WCS_URL = 'https://wcs-slub.pikobytes.de/map/{}'

# Template for the public zoomify tiles
TEMPLATE_PUBLIC_ZOOMIFY_URL = 'https://zoomify-slub.pikobytes.de/zoomify/{}/ImageProperties.xml'

# WMS Service default url template
TEMPLATE_TRANSFORMATION_WMS_URL = 'http://localhost:8080/?map=/etc/mapserver/{}'

# Template string for the public id of a single georefence map
TEMPLATE_PUBLIC_MAP_ID = 'oai:de:slub-dresden:vk:id-{}'

# Template string for the public id of a mosaic map
TEMPLATE_PUBLIC_MOSAIC_MAP_ID = 'oai:de:slub-dresden:vk:mosaic:id-{}'

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
    'sleep_time': 10,
    'wait_on_startup': 1
}

# Settings for logger of the georeference persistent
DAEMON_LOGGER_SETTINGS = {
    'name': 'geoereference-daemon',
    'file': os.path.join(BASE_PATH, '../tmp/daemon.log'),
    'level': logging.DEBUG,
    'formatter': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

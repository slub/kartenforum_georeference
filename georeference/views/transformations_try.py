#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import os
import uuid
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from georeference.models.original_maps import OriginalMap
from georeference.settings import GLOBAL_ERROR_MESSAGE, PATH_MAPFILE_TEMPLATES, PATH_TMP_TRANSFORMATION_ROOT, PATH_TMP_ROOT, PATH_TMP_TRANSFORMATION_DATA_ROOT, TEMPLATE_TRANSFORMATION_WMS_URL
from georeference.utils.georeference import getImageExtent, rectifyImage
from georeference.utils.mapfile import writeMapfile
from georeference.utils.parser import fromPublicOAI, toInt, toGDALGcps
from georeference.utils.validations import isValidClipPolygon, isValidTransformationParams

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@view_config(route_name='transformations_try', renderer='json', request_method='POST', accept='application/json')
def POST_TransformationTryForMapId(request):
    """ Endpoint for processing a temporary georeference result based on the passed transformations parameters and the
        passed original map id.

    :param json_body: Json object containing the transformation parameters
    :type json_body: {{
        map_id: int,
        params: {
            source: str,
            target: str,
            algorithm: str,
            gcps: { source: int[], target: [] }[]
        }
    }}
    :result: JSON object describing the map object
    :rtype: {{
        extent: float[],
        layer_name: str,
        wms_url: str,
    }}
    """
    try:
        if request.method != 'POST':
            return HTTPBadRequest('The endpoint only supports "POST" requests.')

        if request.json_body['map_id'] == None:
            return HTTPBadRequest('Missing map_id')

        # Query mapObj and return error if not exists
        mapId = toInt(fromPublicOAI(request.json_body['map_id']))
        mapObj = OriginalMap.byId(mapId, request.dbsession)
        if mapObj is None:
            return HTTPBadRequest('Could not found map_id')

        # Parse params and validate
        params = request.json_body['params']
        if params is None:
            return HTTPBadRequest('Could not found params.')
        elif isValidTransformationParams(params)[0] == False:
            return HTTPBadRequest(isValidTransformationParams(params)[1])

        # Parse clip
        clip = request.json_body['clip'] if 'clip' in request.json_body else None
        if clip is not None and isValidClipPolygon(clip)[0] == False:
            return HTTPBadRequest(isValidClipPolygon(clip)[1])

        # Parse gcps, srs and create a temporary result
        LOGGER.debug('Create temporary validation result ...')
        gdalGcps = toGDALGcps(params['gcps'])
        srcFile = mapObj.getAbsPath()
        trgFileName = '%s::%s.tif' % (mapObj.file_name, uuid.uuid4())
        trgFile = os.path.abspath(
            os.path.join(
                PATH_TMP_TRANSFORMATION_ROOT,
                trgFileName
            )
        )

        if os.path.exists(srcFile) == False:
            LOGGER.error('Could not found source file %s ...' % srcFile)
            raise

        LOGGER.info('Start processing source file %s ...' % srcFile)

        # Create a rectify image
        rectifyImage(
            srcFile,
            trgFile,
            params['algorithm'],
            gdalGcps,
            params['target'].lower(),
            LOGGER,
            PATH_TMP_ROOT,
            None if clip is None else clip,
        )

        # Create mapfile
        LOGGER.debug('Create temporary map service ...')
        mapfileName = 'wms_%s' % str(uuid.uuid4()).replace('-', '_')
        wmsUrl = TEMPLATE_TRANSFORMATION_WMS_URL % mapfileName
        writeMapfile(
            os.path.join(PATH_TMP_TRANSFORMATION_ROOT, '%s.map' % mapfileName),
            os.path.join(PATH_MAPFILE_TEMPLATES, './wms_dynamic.map'),
            {
                'wmsAbstract': 'This wms is a temporary wms for %s' % mapObj.file_name,
                'wmsUrl': wmsUrl,
                'layerName': mapObj.file_name,
                'layerDataPath': PATH_TMP_TRANSFORMATION_DATA_ROOT % trgFileName,
                'layerProjection': params['target'].lower()
            }
        )
        LOGGER.debug('Return validation result.')

        return {
            'extent': getImageExtent(trgFile),
            'layer_name': mapObj.file_name,
            'wms_url': wmsUrl,
        }
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)
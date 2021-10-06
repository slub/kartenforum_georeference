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
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest, HTTPNotFound
from georeference.utils.georeference import getImageExtent
from georeference.utils.georeference import rectifyImage
from georeference.utils.mapfile import writeMapfile
from georeference.utils.parser import toInt
from georeference.utils.parser import toGDALGcps
from georeference.models.original_maps import OriginalMap
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.settings import GEOREFERENCE_VALIDATION_FOLDER
from georeference.settings import TMP_DIR
from georeference.settings import TEMPLATE_WMS_URL
from georeference.settings import TEMPLATE_WMS_DATA_DIR

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
        mapObj = OriginalMap.byId(toInt(request.json_body['map_id']), request.dbsession)
        if mapObj is None:
            return HTTPBadRequest('Could not found map_id')

        # Validate requests params
        params = request.json_body['params']
        if params is None:
            return HTTPBadRequest('Could not found params.')

        algorithm = params['algorithm']
        gcps = params['gcps']
        source = params['source']
        target = params['target'].lower()
        if algorithm is None:
            return HTTPBadRequest('Missing algorithm')
        if gcps is None or len(gcps) < 3:
            return HTTPBadRequest('Need at least 3 gcps for producing a validation result')
        if source != 'pixel':
            return HTTPBadRequest('Validation endpoint does not support other source type then "pixel"')
        if 'epsg:' not in target:
            return HTTPBadRequest('Validation endpoint expects a epsg code, in the notation "EPSG:4314" for the target type.')

        # Parse gcps, srs and create a temporary result
        LOGGER.debug('Create temporary validation result ...')
        gdalGcps = toGDALGcps(gcps)
        srs = target
        srcFile = mapObj.getAbsPath()
        trgFileName = '%s::%s.tif' % (mapObj.file_name, uuid.uuid4())
        trgFile = os.path.abspath(
            os.path.join(
                GEOREFERENCE_VALIDATION_FOLDER,
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
            algorithm,
            gdalGcps,
            srs,
            LOGGER,
            TMP_DIR,
            None,
        )

        # Create mapfile
        LOGGER.debug('Create temporary map service ...')
        mapfileName = 'wms_%s.map' % uuid.uuid4()
        wmsUrl = TEMPLATE_WMS_URL % mapfileName
        writeMapfile(
            os.path.join(GEOREFERENCE_VALIDATION_FOLDER, mapfileName),
            os.path.join(BASE_PATH, '../templates/wms_dynamic.map'),
            {
                'wmsAbstract': 'This wms is a temporary wms for %s' % mapObj.file_name,
                'wmsUrl': wmsUrl,
                'layerName': mapObj.file_name,
                'layerDataPath': TEMPLATE_WMS_DATA_DIR % trgFileName,
                'layerProjection': target
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
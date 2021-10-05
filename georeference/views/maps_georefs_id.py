#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import json
import os
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest, HTTPNotFound
from georeference.utils.parser import toInt
from georeference.models.transformations import GeoreferenceProcess
from georeference.settings import GLOBAL_ERROR_MESSAGE

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@view_config(route_name='maps_georefs_ids', renderer='json')
def getGeorefsForId(request):
    """ Endpoint for getting a georef process for a given map_id and georef_id. Expects the following url pattern:

        GET     {route_prefix}/map/{map_id}/georefs/{georef_id}

    :param map_id: Id of the map object
    :type map_id: int
    :param georef_id: Georef id.
    :type georef_id: int | str
    :result: JSON object describing the georef process
    :rtype: {{
        clip_polygon: GeoJSON,
        georef_params: *,
        id: int,
        timestamp: str,
        type: 'new' | 'update',
      }}
    """
    try:
        if request.method != 'GET':
            return HTTPBadRequest('The endpoint only supports "GET" requests.')

        if request.matchdict['map_id'] == None or request.matchdict['georef_id'] == None:
            return HTTPBadRequest('Missing map_id or georef_id')

        # Query and return georef process
        georefObj = GeoreferenceProcess.byId(toInt(request.matchdict['georef_id']), request.dbsession)

        if georefObj is None:
            return HTTPNotFound('Could not find georef process for given georef_id')

        return {
            'clip_polygon': georefObj.getClipAsGeoJSON(request.dbsession),
            'georef_params': georefObj.getGeorefParamsAsDict(),
            'id': georefObj.id,
            'timestamp': str(georefObj.timestamp),
            'type': georefObj.type,
        }
    except Exception as e:
        LOGGER.error('Error while trying to process GET request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)

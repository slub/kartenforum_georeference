#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import json
import os
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from ..utils.parser import toInt
from ..models.georeferenzierungsprozess import Georeferenzierungsprozess
from ..models.map import Map
from ..settings import GLOBAL_ERROR_MESSAGE

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@view_config(route_name='maps_georefs', renderer='json', request_method='GET')
def getGeorefs(request):
    """ Endpoint for getting a list of registered georef processes for a given map_id. Expects the following:

        GET     {route_prefix}/map/{map_id}/georefs

    :param map_id: Id of the map object
    :type map_id: int
    :result: JSON object describing the map object
    :rtype: {{
      extent: Extent,
      default_srs: int,
      items: {
        clip_polygon: GeoJSON,
        georef_params: *,
        id: int,
        timestamp: str,
        type: 'new' | 'update',
      }[],
      pending_processes: boolean,
    }}
    """
    try:
        if request.method != 'GET':
            return HTTPBadRequest('The endpoint only supports "GET" requests.')

        if request.matchdict['map_id'] == None:
            return HTTPBadRequest('Missing map_id')

        # query map object and metadata
        mapObj = Map.byId(toInt(request.matchdict['map_id']), request.dbsession)

        # Create default response
        responseObj = {
            'extent': mapObj.getExtent(request.dbsession, 4326) if mapObj.isttransformiert else None,
            'default_srs': 'EPSG:%s' % mapObj.recommendedsrid,
            'items': [],
            'pending_processes': Georeferenzierungsprozess.arePendingProcessForMapId(mapObj.id, request.dbsession)
        }

        # In case there is currently a active georeference process for the map return the id
        for process in request.dbsession.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.mapid == mapObj.id):
            # Create a georeference process object
            responseObj['items'].append({
                'clip_polygon': json.loads(process.getClipAsGeoJson(request.dbsession)),
                'params': process.georefparams,
                'id': process.id,
                'timestamp': str(process.timestamp),
                'type': process.type,
            })

        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to process GET request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)

@view_config(route_name='maps_georefs', renderer='json', request_method='POST')
def postGeorefs(request):
    """ Endpoint for getting a list of registered georef processes for a given map_id. Expects the following:

        POST     {route_prefix}/map/{map_id}/georefs

    :param map_id: Id of the map object
    :type map_id: int

    :result: JSON object describing the map object
    :rtype: {...}

    @TODO - Improve validation off input. Make sure that no incorrect input can be pushed to the database.
    """
    try:
        if request.method != 'POST':
            return HTTPBadRequest('The endpoint only supports "POST" requests.')

        if request.matchdict['map_id'] == None:
            return HTTPBadRequest('Missing map_id')

        return "TODO"
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)




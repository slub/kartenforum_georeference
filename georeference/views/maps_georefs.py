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
import ast
from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from georeference.utils.parser import toInt
from georeference.utils.validations import isValidateGeorefConfirm
from georeference.models.georeference_process import GeoreferenceProcess
from georeference.models.map import Map
from georeference.settings import GLOBAL_ERROR_MESSAGE

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
        hasGeoreferenced = mapObj.getAbsGeorefPath() and os.path.exists(mapObj.getAbsGeorefPath())
        responseObj = {
            'extent': mapObj.getExtent(request.dbsession, 4326) if hasGeoreferenced else None,
            'default_srs': 'EPSG:%s' % mapObj.default_srs,
            'items': [],
            'pending_processes': GeoreferenceProcess.arePendingProcessForMapId(mapObj.id, request.dbsession),
            'enabled_georeference_id': GeoreferenceProcess.getActualGeoreferenceProcessForMapId(mapObj.id, request.dbsession).id
        }

        # Return process for the georeference endpoint
        for process in request.dbsession.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == mapObj.id):
            # Create a georeference process object
            responseObj['items'].append({
                'clip_polygon': process.getClipAsGeoJSON(request.dbsession),
                'params': process.getGeorefParamsAsDict(),
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

@view_config(route_name='maps_georefs', renderer='json', request_method='POST', accept='application/json')
def postGeorefs(request):
    """ Endpoint for POST a new georef process and save it for a given map_id. Expects the following:

        POST     {route_prefix}/map/{map_id}/georefs

    :param map_id: Id of the map object
    :type map_id: int
    :param params: Json object containing the parameters
    :type params: {{
        clip_polygon: GeoJSON,
        georef_params: *,
        type: 'new' | 'update',
        user_id: str,
      }}
    :result: JSON object describing the map object
    :rtype: {...}
    """
    try:
        # Validate request
        if request.method != 'POST':
            return HTTPBadRequest('The endpoint only supports "POST" requests.')
        if request.matchdict['map_id'] == None:
            return HTTPBadRequest('Missing map_id')

        # Validate input
        valid = isValidateGeorefConfirm(request.json_body)
        if valid['isValid'] == False:
            return HTTPBadRequest(valid['errorMsg'])

        # Process response
        mapObj = Map.byId(toInt(request.matchdict['map_id']), request.dbsession)
        clipPolygon = request.json_body['clip_polygon']
        georefParams = request.json_body['georef_params']
        type = request.json_body['type'].lower()
        userId = request.json_body['user_id']

        # If type is "new" make sure that there is no Georeferenprozess request
        if type == 'new' and GeoreferenceProcess.isGeoreferenced(mapObj.id, request.dbsession):
            return HTTPBadRequest('It is forbidden to register a new georeference process for a map, which already has a georeference process registered.')

        # Save to process
        timestamp = datetime.now().isoformat()
        currentGeorefProcess = GeoreferenceProcess.getActualGeoreferenceProcessForMapId(mapObj.id, request.dbsession)
        overwrites = currentGeorefProcess.id if type == 'update' and currentGeorefProcess != None else 0
        newGeorefProcess = GeoreferenceProcess(
            user_id=userId,
            georef_params=json.dumps(georefParams),
            timestamp=timestamp,
            enabled=False,
            type=type,
            overwrites=overwrites,
            validation='',
            processed=False,
            map_id=mapObj.id,
        )

        # Add georef process
        request.dbsession.add(newGeorefProcess)
        request.dbsession.flush()

        if clipPolygon != None:
            newGeorefProcess.setClipFromGeoJSON(
                clipPolygon,
                request.dbsession
            )

        # Build response
        return {
            'id': newGeorefProcess.id,
            'points': int(len(georefParams['gcps'])) * 5,
        }
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)




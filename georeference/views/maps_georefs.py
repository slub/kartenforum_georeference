#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from ..utils.parser import toInt
from ..models.georeferenzierungsprozess import Georeferenzierungsprozess
from ..models.map import Map
from ..settings import GLOBAL_ERROR_MESSAGE

LOGGER = logging.getLogger(__name__)

GENERAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'

@view_config(route_name='maps_georefs', renderer='json')
def getGeorefs(request):
    """ Endpoint for getting a list of registered georef processes for a given mapid. Expects the following:

        GET     {route_prefix}/map/{mapid}/georefs

    :param mapid: Id of the map object
    :type mapid: int
    :result: JSON object describing the map object
    :rtype: {{
      id: int,
      timestamp: str,
      type: 'new' | 'update',

    }[]}
    """
    try:
        if request.method != 'GET' or request.matchdict['mapid'] == None:
            return HTTPBadRequest('Missing mapid')

        # query map object and metadata
        mapObj = Map.by_id(toInt(request.matchdict['mapid']), request.dbsession)

        # Create default response
        responseObj = {
            'extent': mapObj.getExtent(request.dbsession, 4326) if mapObj.isttransformiert else None,
            'default_srs': mapObj.recommendedsrid,
            'items': [],
            'pending_processes': Georeferenzierungsprozess.arePendingProcessForMapId(mapObj.id, request.dbsession)
        }

        # In case there is currently a active georeference process for the map return the id
        for process in request.dbsession.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.mapid == mapObj.id):
            # Create a georeference process object
            responseObj['items'].append({
                'clip_polygon': process.getClipAsGeoJson(request.dbsession),
                'georef_params': process.georefparams,
                'id': process.id,
                'timestamp': str(process.timestamp),
                'type': process.type,
            })

        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to return a GET maps request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)
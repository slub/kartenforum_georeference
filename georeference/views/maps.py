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
from ..models.metadata import Metadata
from ..settings import GLOBAL_ERROR_MESSAGE

LOGGER = logging.getLogger(__name__)

@view_config(route_name='maps', renderer='json')
def getMapsById(request):
    """ Endpoint for accessing map metadata for a given mapid. Expects the following:

        GET     {route_prefix}/map/{mapid}

    :param mapid: Id of the map object
    :type mapid: int
    :result: JSON object describing the map object
    :rtype: {{
      file_name: str,
      georeference_id: int | None,
      id: int,
      map_type: str,
      title_long: str,
      title_short: str,
      zoomify_url: str,
    }}
    """
    try:
        if request.method != 'GET' or request.matchdict['map_id'] == None:
            return HTTPBadRequest('Missing map_id')

        # query map object and metadata
        mapObj = Map.byId(toInt(request.matchdict['map_id']), request.dbsession)
        metadataObj = Metadata.by_id(mapObj.id, request.dbsession)

        # Building basic json response
        responseObj = {
            'file_name': mapObj.apsdateiname,
            'georeference_id': None,
            'id': mapObj.id,
            'map_type': mapObj.maptype,
            'title_long': metadataObj.title,
            'title_short': metadataObj.titleshort,
            'zoomify_url': metadataObj.imagezoomify,
        }

        # In case there is currently a active georeference process for the map return the id
        if Georeferenzierungsprozess.isGeoreferenced(mapObj.id, request.dbsession):
            responseObj['georeference_id'] = Georeferenzierungsprozess.getActualGeoreferenceProcessForMapId(mapObj.id, request.dbsession).id

        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to return a GET maps request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)
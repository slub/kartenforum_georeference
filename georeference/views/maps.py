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
from georeference.utils.parser import toInt
from georeference.models.transformations import Transformation
from georeference.models.original_maps import OriginalMap
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.settings import GLOBAL_ERROR_MESSAGE

LOGGER = logging.getLogger(__name__)

@view_config(route_name='maps', renderer='json')
def getMapsById(request):
    """ Endpoint for accessing map metadata for a given mapid. Expects the following:

        GET     {route_prefix}/map/{map_id}

    :param map_id: Id of the map object
    :type map_id: int
    :result: JSON object describing the map object
    :rtype: {{
      file_name: str,
      transformation_id: int | None,
      map_id: int,
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
        mapObj = OriginalMap.byId(toInt(request.matchdict['map_id']), request.dbsession)
        metadataObj = Metadata.byId(mapObj.id, request.dbsession)

        # Building basic json response
        responseObj = {
            'file_name': mapObj.file_name,
            'transformation_id': None,
            'map_id': mapObj.id,
            'map_type': mapObj.map_type,
            'title_long': metadataObj.title,
            'title_short': metadataObj.titleshort,
            'zoomify_url': metadataObj.imagezoomify,
        }

        # In case there is currently a active georeference process for the map return the id
        georefMapObj = GeorefMap.byOriginalMapId(mapObj.id, request.dbsession)
        if georefMapObj != None:
            responseObj['transformation_id'] = georefMapObj.transformation_id

        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to return a GET maps request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)
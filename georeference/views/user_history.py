#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from sqlalchemy import desc

LOGGER = logging.getLogger(__name__)

from georeference.settings import OAI_ID_PATTERN
from georeference.models.georeference_process import GeoreferenceProcess
from georeference.models.map import Map
from georeference.models.metadata import Metadata

GENERAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'

@view_config(route_name='user_history', renderer='json')
def generateGeoreferenceHistory(request):
    if request.method != 'GET':
        return HTTPBadRequest('The endpoint only supports "GET" requests.')

    if request.matchdict['user_id'] == None:
        return HTTPBadRequest('Missing user_id')

    try:
        LOGGER.debug('Query georeference profile information from database for user %s' % request.matchdict['user_id'])
        queryData = request.dbsession.query(GeoreferenceProcess, Metadata, Map).join(Metadata, GeoreferenceProcess.map_id == Metadata.mapid)\
            .join(Map, GeoreferenceProcess.map_id == Map.id)\
            .filter(GeoreferenceProcess.user_id == request.matchdict['user_id'])\
            .order_by(desc(GeoreferenceProcess.id))

        LOGGER.debug('Create response list')
        georef_profile = []
        points = 0
        for record in queryData:
            georef = record[0]
            metadata = record[1]
            mapObj = record[2]

            #
            # create response
            #
            responseRecord = {'georefid': georef.id, 'mapid': OAI_ID_PATTERN % georef.map_id,
                              'georefparams': georef.getGeorefParamsAsDict(), 'time': str(metadata.timepublish),
                              'transformed': georef.processed,
                              'isvalide': georef.validation, 'title': metadata.title, 'key': mapObj.file_name,
                              'georeftime': str(georef.timestamp), 'type': georef.type,
                              'published': georef.processed, 'thumbnail': metadata.thumbsmid}

            # add boundingbox if exists
            if mapObj.boundingbox is not None:
                responseRecord['boundingbox'] = mapObj.getExtentAsString(request.dbsession, 4326)

            # calculate points
            if georef.validation != 'invalide':
                points += 20

            georef_profile.append(responseRecord)

        LOGGER.debug('Response: %s'%georef_profile)

        return {'georef_profile':georef_profile, 'points':points}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GENERAL_ERROR_MESSAGE)
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

from ..settings import OAI_ID_PATTERN
from ..models.georeferenzierungsprozess import Georeferenzierungsprozess
from ..models.map import Map
from ..models.metadata import Metadata

GENERAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'

@view_config(route_name='user_history', renderer='json')
def generateGeoreferenceHistory(request):

    def getUserId(request):
        """ Parse the process id from the request.

        :type request: pyramid.request
        :return: str|None """
        if request.method == 'GET' and 'userid' in request.matchdict:
            return request.matchdict['userid']
        return None

    LOGGER.info('Request - Get georeference profile page.')

    # Try to get the user id
    userid = getUserId(request)
    if userid is None:
        raise HTTPBadRequest("Wrong or missing userid.")

    try:
        LOGGER.debug('Query georeference profile information from database for user %s'%userid)
        queryData = request.dbsession.query(Georeferenzierungsprozess, Metadata, Map).join(Metadata, Georeferenzierungsprozess.mapid == Metadata.mapid)\
            .join(Map, Georeferenzierungsprozess.mapid == Map.id)\
            .filter(Georeferenzierungsprozess.nutzerid == userid)\
            .order_by(desc(Georeferenzierungsprozess.id))

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
            responseRecord = {'georefid':georef.id, 'mapid':OAI_ID_PATTERN%georef.mapid,
                    'georefparams': georef.georefparams, 'time': str(metadata.timepublish), 'transformed': georef.processed,
                    'isvalide': georef.adminvalidation, 'title': metadata.title, 'key': mapObj.apsdateiname,
                    'georeftime':str(georef.timestamp),'type':georef.type,
                    'published':georef.processed, 'thumbnail': metadata.thumbsmid}

            # add boundingbox if exists
            if mapObj.boundingbox is not None:
                responseRecord['boundingbox'] = mapObj.getExtentAsString(request.dbsession, 4326)

            # calculate points
            if georef.adminvalidation != 'invalide':
                points += 20

            georef_profile.append(responseRecord)

        LOGGER.debug('Response: %s'%georef_profile)

        return {'georef_profile':georef_profile, 'points':points}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information');
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GENERAL_ERROR_MESSAGE)
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

from georeference.models.transformations import Transformation, ValidationValues
from georeference.models.original_maps import OriginalMap
from georeference.models.metadata import Metadata
from georeference.models.georef_maps import GeorefMap
from georeference.utils.parser import toPublicOAI

GENERAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'

@view_config(route_name='user_history', renderer='json')
def generateGeoreferenceHistory(request):
    if request.method != 'GET':
        return HTTPBadRequest('The endpoint only supports "GET" requests.')

    if request.matchdict['user_id'] == None:
        return HTTPBadRequest('Missing user_id')

    try:
        LOGGER.debug('Query georeference profile information from database for user %s' % request.matchdict['user_id'])
        queryData = request.dbsession.query(Transformation, Metadata, OriginalMap, GeorefMap)\
            .join(Metadata, Transformation.original_map_id == Metadata.original_map_id)\
            .join(OriginalMap, Transformation.original_map_id == OriginalMap.id) \
            .join(GeorefMap, GeorefMap.transformation_id == Transformation.id, full=True) \
            .filter(Transformation.user_id == request.matchdict['user_id'])\
            .order_by(desc(Transformation.id))

        LOGGER.debug('Create response list')
        georef_profile = []
        points = 0
        for record in queryData:
            transformationObj = record[0]
            metadataObj = record[1]
            mapObj = record[2]
            georefMapObj = record[3]

            # Create response
            responseRecord = {
                'file_name': mapObj.file_name,
                'is_transformed': True if georefMapObj != None else False,
                'map_id': toPublicOAI(mapObj.id),
                'transformation': {
                    'id': transformationObj.id,
                    'params': transformationObj.getParamsAsDict(),
                    'submitted': str(transformationObj.submitted),
                    'validation': transformationObj.validation
                },
                'metadata': {
                    'thumbnail': metadataObj.link_thumb_mid,
                    'time_published': str(metadataObj.time_of_publication),
                    'title': metadataObj.title,
                }
            }

            # calculate points
            if transformationObj.validation != ValidationValues.INVALID.value:
                points += 20

            georef_profile.append(responseRecord)

        LOGGER.debug('Response: %s'%georef_profile)

        return {'georef_profile':georef_profile, 'points':points}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GENERAL_ERROR_MESSAGE)
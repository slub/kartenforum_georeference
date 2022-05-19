#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError
from sqlalchemy import desc
from sqlalchemy import func
from georeference.models.transformations import Transformation, EnumValidationValue
from georeference.models.georef_maps import GeorefMap
from georeference.models.raw_maps import RawMap
from georeference.settings import GLOBAL_ERROR_MESSAGE

LOGGER = logging.getLogger(__name__)


@view_config(route_name='statistics', renderer='json', request_method='GET')
def GET_statistics(request):
    LOGGER.info('Request - Get georeference points.')
    LOGGER.debug(request)

    try:
        #
        # Create the database queries
        #

        # Query number of georeference processes for each user
        q_points = request.dbsession.query(
            Transformation.user_id.label('user'), func.count(Transformation.user_id).label('occurrence')
        ) \
            .filter(Transformation.validation != EnumValidationValue.INVALID.value) \
            .group_by(Transformation.user_id) \
            .subquery()

        # Query number of valid transformations for each user of type "new"
        q_new = request.dbsession.query(Transformation.user_id.label('user'),
                                        func.count(Transformation.params).label('transformations')) \
            .filter(Transformation.validation != EnumValidationValue.INVALID.value) \
            .filter(Transformation.overwrites == 0) \
            .group_by(Transformation.user_id) \
            .subquery()

        # Query number of valid transformations for each user of type "update"
        q_update = request.dbsession.query(Transformation.user_id.label('user'),
                                           func.count(Transformation.params).label('transformations')) \
            .filter(Transformation.validation != EnumValidationValue.INVALID.value) \
            .filter(Transformation.overwrites > 0) \
            .group_by(Transformation.user_id) \
            .subquery()

        # Query the data
        data = request.dbsession.query(q_points.c.user, q_points.c.occurrence, q_new.c.transformations,
                                       q_update.c.transformations) \
            .outerjoin(q_new, q_points.c.user == q_new.c.user) \
            .outerjoin(q_update, q_points.c.user == q_update.c.user) \
            .order_by(desc(q_points.c.occurrence)).limit(20)

        # Create ranking list
        user_points = []
        for record in data:
            userid = record[0]
            points = record[1] * 20
            new = record[2] if record[2] is not None else 0
            update = record[3] if record[3] is not None else 0
            user_points.append({'user_id': userid, 'total_points': points, 'transformation_new': new,
                                'transformation_updates': update})

        LOGGER.debug('Get georeference map count')
        georeference_map_count = request.dbsession.query(GeorefMap.raw_map_id).count()

        LOGGER.debug('Get missing georeference map count')
        missing_georeference_map_count = request.dbsession.query(RawMap) \
            .join(GeorefMap, GeorefMap.raw_map_id == RawMap.id, full=True) \
            .filter(GeorefMap.raw_map_id == None) \
            .count()

        return {'georeference_points': user_points, 'georeference_map_count': georeference_map_count,
                'not_georeference_map_count': missing_georeference_map_count}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)

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
from ..models.georeferenzierungsprozess import Georeferenzierungsprozess
from ..models.map import Map

LOGGER = logging.getLogger(__name__)

GENERAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'

@view_config(route_name='summary_georeference', renderer='json')
def getGeoreferencePoints(request):
    LOGGER.info('Request - Get georeference points.')
    LOGGER.debug(request)
    try:
        #
        # Create the database queries
        #

        # Query number of valide georeference processes for each user
        qPoints = request.dbsession.query(Georeferenzierungsprozess.nutzerid.label('user'),
                func.count(Georeferenzierungsprozess.nutzerid).label('occurrence'))\
            .filter(Georeferenzierungsprozess.adminvalidation != 'invalide')\
            .group_by(Georeferenzierungsprozess.nutzerid)\
            .subquery()

        # Query number of valide georeference processes for each user with type "new"
        qNew = request.dbsession.query(Georeferenzierungsprozess.nutzerid.label('user'), func.count(Georeferenzierungsprozess.type).label('type'))\
                    .filter(Georeferenzierungsprozess.adminvalidation != 'invalide')\
                    .filter(Georeferenzierungsprozess.type == 'new')\
                    .group_by(Georeferenzierungsprozess.nutzerid)\
                    .subquery()

        # Query number of valide georeference processes for each user with type "update"
        qUpdate = request.dbsession.query(Georeferenzierungsprozess.nutzerid.label('user'), func.count(Georeferenzierungsprozess.type).label('type'))\
                    .filter(Georeferenzierungsprozess.adminvalidation != 'invalide')\
                    .filter(Georeferenzierungsprozess.type == 'update')\
                    .group_by(Georeferenzierungsprozess.nutzerid)\
                    .subquery()

        # Query the data
        data = request.dbsession.query(qPoints.c.user, qPoints.c.occurrence, qNew.c.type, qUpdate.c.type)\
                .outerjoin(qNew, qPoints.c.user == qNew.c.user)\
                .outerjoin(qUpdate, qPoints.c.user == qUpdate.c.user)\
                .order_by(desc(qPoints.c.occurrence)).limit(20)

        # Create ranking list
        user_points = []
        for record in data:
            userid = record[0]
            points = record[1] * 20
            new = record[2] if record[2] is not None else 0
            update = record[3] if record[3] is not None else 0
            user_points.append({'userid':userid, 'points': points, 'new': new, 'update': update})

        LOGGER.debug('Get georeference map count')
        queryData = request.dbsession.query(func.count(Map.isttransformiert))\
            .filter(Map.isttransformiert == True)\
            .filter(Map.istaktiv == True)
        georeference_map_count = []
        for record in queryData:
            georeference_map_count = record[0]

        LOGGER.debug('Get missing georeference map count')
        queryData = request.dbsession.query(func.count(Map.isttransformiert))\
            .filter(Map.isttransformiert == False)\
            .filter(Map.istaktiv == True)
        missing_georeference_map_count = []
        for record in queryData:
            missing_georeference_map_count = record[0]

        return {'pointoverview': user_points, 'georeference_map_count': georeference_map_count, 'missing_georeference_map_count':missing_georeference_map_count}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GENERAL_ERROR_MESSAGE)
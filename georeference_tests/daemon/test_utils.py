#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 21.02.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
from georeference.models.georef_maps import GeorefMap
from georeference.models.transformations import Transformation
from georeference.daemon.utils import getGeometry

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_getGeometry_useClipPolygon(dbsession_only):
    """ The test checks if checks the clip polygon is used for geometry if set.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    mapId = 10007521

    # Build test request
    subject = getGeometry(mapId, dbsession_only)

    assert subject['type'] == "Polygon"

def test_getGeometry_useExtentPolygon(dbsession_only):
    """ The test checks if checks the extent is used for geometry if clip polygon is not set.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    mapId = 10007521

    # Get relevant data objects
    georefMap = GeorefMap.byOriginalMapId(mapId, dbsession_only)

    # Set transformation to null
    transformation = Transformation.byId(georefMap.transformation_id, dbsession_only)
    transformation.clip = None

    # Build test request
    subject = getGeometry(mapId, dbsession_only)
    assert subject['type'] == "Polygon"

    dbsession_only.rollback()
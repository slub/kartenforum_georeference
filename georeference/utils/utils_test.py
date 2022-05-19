#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from datetime import datetime
from .utils import get_tms_directory, get_geometry
from georeference.models.raw_maps import RawMap
from georeference.models.georef_maps import GeorefMap
from georeference.models.transformations import Transformation, EnumValidationValue

def test_get_geometry_use_clip_polygon(dbsession_only):
    """ The test checks if checks the clip polygon is used for geometry if set.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    map_id = 10007521

    # Build test request
    subject = get_geometry(map_id, dbsession_only)

    assert subject['type'] == "Polygon"

def test_get_geometry_use_clip_polygon_from_multipolygon(dbsession_only):
    """ The test checks if checks the clip polygon is used for geometry if set.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    map_id = 10007521
    transformation_id = 8999

    dbsession_only.add(
        Transformation(
            id=transformation_id,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params=json.dumps({"source": "pixel", "target": "EPSG:4326", "algorithm": "affine", "gcps": [{"source": [4719, 1380], "target": [10.714308619959, 48.755628213793]}, {"source": [2809, 1340], "target": [10.669971704948, 48.755836873379]}, {"source": [1414, 964], "target": [10.636985302208, 48.76146858635]}, {"source": [988, 3018], "target": [10.627818108085, 48.729436326083]}, {"source": [2885, 5235], "target": [10.672315955649, 48.695646899534]}, {"source": [6063, 4201], "target": [10.746548176053, 48.712192253709]}, {"source": [2739, 3238], "target": [10.668661594173, 48.726582481426]}, {"source": [1664, 4171], "target": [10.643736719976, 48.711748022874]}, {"source": [5797, 746], "target": [10.739638209288, 48.765643779367]}, {"source": [6125, 4814], "target": [10.748037099729, 48.70257582834]}]}),
            clip=json.dumps({"type":"Polygon","coordinates":[[[14.799189345,50.89943374],[14.811818315,50.899957856],[14.812090785,50.892868908],[14.797718009,50.892877501],[14.797690762,50.892765788],[14.797949608,50.892774382],[14.799189345,50.89943374]]]}),
            target_crs=4326,
            validation=EnumValidationValue.VALID.value,
            raw_map_id=map_id,
            overwrites=0,
            comment=None
        )
    )
    dbsession_only.flush()

    # Update temporary reference of the current georef id
    georef_map_obj = GeorefMap.by_raw_map_id(map_id, dbsession_only)
    georef_map_obj.transformation_id = transformation_id

    # Build test request
    subject = get_geometry(map_id, dbsession_only)

    assert subject['type'] == "Polygon"

def test_get_geometry_use_extent_polygon(dbsession_only):
    """ The test checks if checks the extent is used for geometry if clip polygon is not set.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    map_id = 10007521

    # Get relevant data objects
    georef_map = GeorefMap.by_raw_map_id(map_id, dbsession_only)

    # Set transformation to null
    transformation = Transformation.by_id(georef_map.transformation_id, dbsession_only)
    transformation.clip = None

    # Build test request
    subject = get_geometry(map_id, dbsession_only)
    assert subject['type'] == "Polygon"

    dbsession_only.rollback()


def test_get_tms_directory_success():
    """ Checks if the function returns correct string. """
    dummy_raw_map_obj = RawMap(
        id=1,
        file_name='df_dk_0010001_3352_191s8',
        enabled=False,
        map_type='M',
        default_crs=4314,
        rel_path='',
    )
    subject = get_tms_directory(dummy_raw_map_obj)

    assert isinstance(subject, str) == True
    assert 'm/df_dk_0010001_3352_191s8' in subject

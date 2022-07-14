#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import json
from datetime import datetime
from georeference.jobs.process_transformation import run_process_new_transformation
from georeference.models.georef_maps import GeorefMap
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.raw_maps import RawMap
from georeference.models.transformations import Transformation, EnumValidationValue
from georeference.settings import ES_ROOT, ES_INDEX_NAME
from georeference.utils.es_index import get_es_index
from georeference.utils.parser import to_public_map_id

# Initialize the logger
LOGGER = logging.getLogger(__name__)


def test_run_process_jobs_success(dbsession_only):
    """ The test checks the proper running of the process jobs

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    map_id = 10010367
    new_job = Job(
        id=10000000,
        submitted=datetime.now().isoformat(),
        user_id='test',
        type=EnumJobType.TRANSFORMATION_PROCESS.value,
        description='{ "transformation_id": 10000001 }',
        state=EnumJobState.NOT_STARTED.value
    )
    dbsession_only.add(
        Transformation(
            id=10000001,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params=json.dumps({
                "source": "pixel",
                "target": "EPSG:4314",
                "algorithm": "affine",
                "gcps": [{"source": [592, 964], "target": [16.499998092651, 51.900001525879]},
                         {"source": [588, 7459], "target": [16.499998092651, 51.79999923706]},
                         {"source": [7291, 7459], "target": [16.666667938232, 51.79999923706]},
                         {"source": [7289, 972], "target": [16.666667938232, 51.900001525879]}]
            }),
            target_crs=4314,
            validation=EnumValidationValue.MISSING.value,
            raw_map_id=map_id,
            overwrites=0,
            comment=None,
            clip=json.dumps({
                "crs": {"type": "name", "properties": {"name": "EPSG:4314"}},
                "coordinates": [[
                    [16.5000353928, 51.900032347], [16.4999608259, 51.7999684435],
                    [16.666705251, 51.8000300686], [16.6666305921, 51.8999706667],
                    [16.5000353928, 51.900032347]
                ]],
                "type": "Polygon"
            })
        )
    )
    dbsession_only.flush()
    dbsession_only.add(new_job)
    dbsession_only.flush()

    # Normally the tms processing needs really long. To prevent this we temporary increase the map_scale of the RawMap
    # to trigger lower zoom levels
    raw_map_obj = RawMap.by_id(map_id, dbsession_only)
    raw_map_obj.map_scale = 1000000000
    dbsession_only.flush()

    # Get the index object
    es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)

    # Build test request
    run_process_new_transformation(
        es_index,
        dbsession_only,
        LOGGER,
        new_job
    )

    # Check if the database changes are correct
    g = dbsession_only.query(GeorefMap).filter(GeorefMap.transformation_id == 10000001).first()
    assert g is not None

    # Check if the index was pushed to the es
    assert es_index.get(ES_INDEX_NAME, id=to_public_map_id(map_id)) is not None

    dbsession_only.rollback()
    es_index.close()

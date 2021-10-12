#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 16.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import json
from datetime import datetime
from georeference.models.georef_maps import GeorefMap
from georeference.models.jobs import Job, TaskValues
from georeference.models.transformations import Transformation, ValidationValues
from georeference.daemon.jobs import getUnprocessedJobs
from georeference.daemon.jobs import runProcessJobs
from georeference.daemon.jobs import runValidationJobs
from georeference.daemon.jobs import loadInitialData
from georeference.settings import ES_ROOT
from georeference.settings import ES_INDEX_NAME
from georeference.scripts.es import getIndex
from georeference.utils.parser import toPublicOAI

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_getUnprocessedJobs_success(dbsession_only):
    """ The test checks if the function "getUnprocessedJobs" returns the correct jobs and clears the race conditions.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    mapId = 10007521
    dbsession_only.add(
        Transformation(
            id=1,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params="",
            validation=ValidationValues.MISSING.value,
            original_map_id=mapId,
            overwrites=0,
            comment=None
        )
    )
    dbsession_only.add(
        Transformation(
            id=2,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params="",
            validation=ValidationValues.MISSING.value,
            original_map_id=mapId,
            overwrites=0,
            comment=None
        )
    )
    dbsession_only.flush()
    dbsession_only.add(
        Job(
            id=1,
            processed=False,
            submitted=datetime.now().isoformat(),
            user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 1 }'
        )
    )
    dbsession_only.add(
        Job(
            id=2,
            processed=False,
            submitted=datetime.now().isoformat(),
            user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 2 }'
        )
    )
    dbsession_only.add(
        Job(
            id=3,
            processed=True,
            submitted=datetime.now().isoformat(),
            user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 2 }'
        )
    )
    dbsession_only.add(
        Job(
            id=4,
            processed=False,
            submitted=datetime.now().isoformat(),
            user_id='test',
            task_name=TaskValues.TRANSFORMATION_SET_VALID.value,
            task='{ "transformation_id": 2  }'
        )
    )
    dbsession_only.flush()

    # Build test request
    subject = getUnprocessedJobs(dbsession_only, logger=LOGGER)
    assert len(subject['process']) == 1
    assert subject['process'][0].id == 2
    assert len(subject['validation']) == 1

    dbsession_only.rollback()

def test_runProcessJobs_success(dbsession_only):
    """ The test checks the proper running of the process jobs

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    mapId = 10010367
    newJob = Job(
        id=1,
        processed=False,
        submitted=datetime.now().isoformat(),
        user_id='test',
        task_name=TaskValues.TRANSFORMATION_PROCESS.value,
        task='{ "transformation_id": 1 }'
    )
    dbsession_only.add(
        Transformation(
            id=1,
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
            validation=ValidationValues.MISSING.value,
            original_map_id=mapId,
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
    dbsession_only.add(newJob)
    dbsession_only.flush()

    # Get the index object
    esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=True, logger=LOGGER)

    # Build test request
    subject = runProcessJobs(
        getUnprocessedJobs(dbsession_only, logger=LOGGER)['process'],
        esIndex,
        dbsession_only,
        logger=LOGGER
    )

    # Check the correct job count
    assert len(subject['processed_transformations']) == 1

    # Check if the database changes are correct
    g = dbsession_only.query(GeorefMap).filter(GeorefMap.transformation_id == 1).first()
    assert g != None

    # Check if the index was pushed to the es
    assert esIndex.get(ES_INDEX_NAME, id=toPublicOAI(mapId)) != None

    dbsession_only.rollback()

def test_runValidationJobs_success_withOverwrite(dbsession_only):
    """ The test checks the proper processing of a validation job. The newer invalid transformation, should be replaced by an older
        valid transformation.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    mapId = 10007521
    transformationId = 12187
    newJob = Job(
        id=1,
        processed=False,
        submitted=datetime.now().isoformat(),
        user_id='test',
        task_name=TaskValues.TRANSFORMATION_SET_INVALID.value,
        task='{ "transformation_id": %s }' % transformationId
    )
    dbsession_only.add(newJob)
    dbsession_only.flush()

    # Get the index object
    esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=True, logger=LOGGER)

    # Build test request
    subject = runValidationJobs(
        getUnprocessedJobs(dbsession_only, logger=LOGGER)['validation'],
        esIndex,
        dbsession_only,
        logger=LOGGER
    )

    # Check the correct job count
    assert len(subject['validation_transformations']) == 1

    # Query if the database was changed correctly
    t = dbsession_only.query(Transformation).filter(Transformation.id == transformationId).first()
    assert t != None
    assert t.validation == ValidationValues.INVALID.value

    # Check if the database changes are correct
    g = dbsession_only.query(GeorefMap).filter(GeorefMap.transformation_id == t.overwrites).first()
    assert g != None
    assert g.transformation_id == t.overwrites

    # Check if the index was pushed to the es
    esDoc = esIndex.get(ES_INDEX_NAME, id=toPublicOAI(mapId))
    assert esDoc != None
    assert esDoc['_source']['geometry'] != None

    dbsession_only.rollback()

def test_runValidationJobs_success_withoutOverwrite(dbsession_only):
    """ The test checks the proper processing of a validation job. The transformation is set to invalid and there is no more valid transformation.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    mapId = 10009482
    transformationId = 7912
    newJob = Job(
        id=1,
        processed=False,
        submitted=datetime.now().isoformat(),
        user_id='test',
        task_name=TaskValues.TRANSFORMATION_SET_INVALID.value,
        task='{ "transformation_id": %s }' % transformationId
    )
    dbsession_only.add(newJob)
    dbsession_only.flush()

    # Get the index object
    esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=True, logger=LOGGER)

    # Build test request
    subject = runValidationJobs(
        getUnprocessedJobs(dbsession_only, logger=LOGGER)['validation'],
        esIndex,
        dbsession_only,
        logger=LOGGER
    )

    # Check the correct job count
    assert len(subject['validation_transformations']) == 1

    # Query if the database was changed correctly
    t = dbsession_only.query(Transformation).filter(Transformation.id == transformationId).first()
    assert t != None
    assert t.validation == ValidationValues.INVALID.value

    # Check if the database changes are correct
    g = dbsession_only.query(GeorefMap).filter(GeorefMap.original_map_id == mapId).first()
    assert g == None

    # Check if the index was pushed to the es
    esDoc = esIndex.get(ES_INDEX_NAME, id=toPublicOAI(mapId))
    assert esDoc != None
    assert esDoc['_source']['geometry'] == None

    dbsession_only.rollback()

def test_loadInitialData_success(dbsession_only):
     success = loadInitialData(dbsession_only, LOGGER)
     assert success == True
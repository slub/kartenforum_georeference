#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 16.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import json
from datetime import datetime
from georeference.models.georeference_process import GeoreferenceProcess
from georeference.models.map import Map
from georeference.daemon.jobs import runInitializationJob
from georeference.daemon.jobs import runNewJobs
from georeference.daemon.jobs import runUpdateJobs
from georeference.settings import ES_ROOT
from georeference.settings import ES_INDEX_NAME
from georeference.scripts.es import getIndex

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_runNewJobs_success(dbsession_only):
    # Create test data
    mapId = 10010367
    georefId = 10000000
    newGeorefProcess = GeoreferenceProcess(
        id=georefId,
        timestamp=datetime.now().isoformat(),
        type='new',
        user_id='user_1',
        enabled=False,
        processed=False,
        georef_params=json.dumps({
            "source": "pixel",
            "target": "EPSG:4314",
            "algorithm": "affine",
            "gcps": [{"source": [592, 964], "target": [16.499998092651, 51.900001525879]},
                          {"source": [588, 7459], "target": [16.499998092651, 51.79999923706]},
                          {"source": [7291, 7459], "target": [16.666667938232, 51.79999923706]},
                          {"source": [7289, 972], "target": [16.666667938232, 51.900001525879]}]
        }),
        validation='',
        overwrites=0,
        map_id=mapId,
    )
    dbsession_only.add(newGeorefProcess)
    dbsession_only.flush()

    newGeorefProcess.setClipFromGeoJSON({
        "crs": {"type": "name", "properties": {"name": "EPSG:4314"}},
        "coordinates": [[
            [16.5000353928, 51.900032347], [16.4999608259, 51.7999684435],
            [16.666705251, 51.8000300686], [16.6666305921, 51.8999706667],
            [16.5000353928, 51.900032347]
        ]],
        "type": "Polygon"
    }, dbsession_only)

    # Run the test job
    jobCount = runNewJobs(dbsession_only, LOGGER)

    # There should be one job processed
    assert jobCount == 1

    # Check if the database changes are correct
    g = GeoreferenceProcess.byId(georefId, dbsession_only)
    assert g.enabled == True
    assert g.processed == True

    m = Map.byId(mapId, dbsession_only)
    assert m.getAbsGeorefPath() != None

    # Check if the index was pushed to the es
    esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=False, logger=LOGGER)
    assert esIndex.get(ES_INDEX_NAME, id=mapId) != None

    dbsession_only.rollback()

def test_runUpdateJobs_success(dbsession_only):
    # Create test data
    mapId = 10001556
    georefId = 10000000
    overwriteGeorefId = 11823
    newGeorefProcess = GeoreferenceProcess(
        id=georefId,
        timestamp=datetime.now().isoformat(),
        type='update',
        user_id='user_1',
        enabled=False,
        processed=False,
        georef_params=json.dumps({"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]}, {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}, {"source": [6969, 3160], "target": [14.816612768409, 50.863606051111]}, {"source": [1907, 1301], "target": [14.690521818997, 50.891860483128]}, {"source": [4180, 4396], "target": [14.747856876595, 50.843955582846]}, {"source": [5070, 5489], "target": [14.769772087663, 50.827125251053]}, {"source": [6933, 7171], "target": [14.816342007402, 50.801483295161]}, {"source": [3325, 7152], "target": [14.727274235239, 50.801026963158]}, {"source": [1509, 6622], "target": [14.681454720195, 50.808715847718]}]}),
        validation='',
        overwrites=overwriteGeorefId,
        map_id=mapId,
    )
    dbsession_only.add(newGeorefProcess)
    dbsession_only.flush()

    newGeorefProcess.setClipFromGeoJSON(
        {"type":"Polygon","crs":{"type":"name","properties":{"name":"EPSG:4314"}},"coordinates":[[[14.66364715,50.899831877],[14.661734495,50.799776765],[14.76482527,50.800276974],[14.76601098,50.800290518],[14.766134477,50.790482954],[14.782466161,50.790564091],[14.782294867,50.800358074],[14.829388684,50.800594678],[14.829132977,50.900185772],[14.829130294,50.900185772],[14.66364715,50.899831877]]]},
        dbsession_only
   )

    # Run the test job
    jobCount = runUpdateJobs(dbsession_only, LOGGER)

    # There should be one job processed
    assert jobCount == 1

    # Check if the database changes are correct
    gNew = GeoreferenceProcess.byId(georefId, dbsession_only)
    assert gNew.enabled == True
    assert gNew.processed == True
    gOld = GeoreferenceProcess.byId(overwriteGeorefId, dbsession_only)
    assert gOld.enabled == False

    m = Map.byId(mapId, dbsession_only)
    assert m.getAbsGeorefPath() != None

    # Check if the index was pushed to the es
    esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=False, logger=LOGGER)
    assert esIndex.get(ES_INDEX_NAME, id=mapId) != None

    dbsession_only.rollback()

# def test_runInitializationJob_success(dbsession_only):
#     success = runInitializationJob(dbsession_only, LOGGER)
#     dbsession_only.rollback()
#     assert success == True
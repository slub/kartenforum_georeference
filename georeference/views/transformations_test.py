#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from datetime import datetime
from georeference.models.raw_maps import RawMap
from georeference.models.transformations import Transformation, EnumValidationValue
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.settings import ROUTE_PREFIX
from georeference.utils.parser import to_public_map_id


def test_GET_transformations_for_map_id_success(testapp, dbsession):
    map_id = 10001556

    # Insert an unprocessed job for the map_id
    dbsession.add(
        Transformation(
            id=1,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params=json.dumps({'source': 'pixel', 'target': 'EPSG:4314', 'algorithm': 'tps', 'gcps': [
                {'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}
            ]}),
            clip=json.dumps({
                'type': 'Polygon',
                'coordinates': [
                    [[13.71812582, 51.074800786], [13.709993362, 51.060460491], [13.703641892, 51.049528679],
                     [13.751320839, 51.038047836], [13.76591742, 51.063727394], [13.749228716, 51.067503095],
                     [13.71812582, 51.074800786]]],
                'crs': {'type': 'name', 'properties': {'name': 'EPSG:4314'}}
            }),
            target_crs=4314,
            validation=EnumValidationValue.MISSING.value,
            raw_map_id=10001556,
            overwrites=0,
            comment=None
        )
    )
    dbsession.add(
        Job(
            id=1,
            submitted=datetime.now().isoformat(),
            user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 1 }',
            state=EnumJobState.NOT_STARTED.value
        )
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(ROUTE_PREFIX + f'/transformations?map_id={to_public_map_id(map_id)}&additional_properties=true',
                      status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 5
    assert res.json['additional_properties']['pending_jobs'] == True

    # Check proper transformation of the target_crs
    transformation_subject = res.json['transformations'][0]
    assert transformation_subject['params']['target'] == 'EPSG:4326'
    assert len(transformation_subject['params']['gcps']) == 4
    assert round(transformation_subject['params']['gcps'][0]['target'][0], 6) == round(14.807667264759935, 6)
    assert round(transformation_subject['params']['gcps'][0]['target'][1], 6) == round(50.89598748103341, 6)

    # Check proper coordinate system of the clip polygon
    assert transformation_subject['clip']['crs']['properties']['name'] == 'EPSG:4326'
    dbsession.rollback()


def test_GET_transformations_for_map_id_success_empty_result(testapp):
    # Build test request
    res = testapp.get(ROUTE_PREFIX + f'/transformations?map_id={to_public_map_id(10003265)}&additional_properties=true',
                      status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 0


def test_GET_transformations_for_map_id_success_two_results(testapp):
    # Build test request
    res = testapp.get(ROUTE_PREFIX + f'/transformations?map_id={to_public_map_id(10009466)}&additional_properties=true',
                      status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 2


def test_GET_transformations_for_map_id_success_transformations_only_invalid(testapp, dbsession):
    map_id = 10001556

    # Insert an unprocessed job for the map_id
    dbsession.add(
        Transformation(
            id=1,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params=json.dumps({'source': 'pixel', 'target': 'EPSG:4314', 'algorithm': 'tps', 'gcps': []}),
            target_crs=4314,
            validation=EnumValidationValue.INVALID.value,
            raw_map_id=map_id,
            overwrites=0,
            comment=None
        )
    )
    dbsession.add(
        Job(
            id=1,
            submitted=datetime.now().isoformat(),
            user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 1 }',
            state=EnumJobState.NOT_STARTED.value
        )
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(
        ROUTE_PREFIX + f'/transformations?map_id={to_public_map_id(map_id)}&additional_properties=false&validation={EnumValidationValue.INVALID.value}',
        status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 1
    assert 'additional_properties' not in res.json

    dbsession.rollback()


def test_GET_transformations_success_for_validation_state_empty_result(testapp):
    res = testapp.get(ROUTE_PREFIX + '/transformations?validation=test', status=400)
    assert res.status_int == 400


def test_GET_transformations_success_for_validation_state_missing(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + f'/transformations?validation={EnumValidationValue.MISSING.value.upper()}',
                      status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 4


def test_GET_transformations_success_for_validation_state_valid(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + f'/transformations?validation={EnumValidationValue.VALID.value}', status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 18


def test_GET_transformations_success_for_validation_state_invalid(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + f'/transformations?validation={EnumValidationValue.INVALID.value}', status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 1


def test_GET_transformations_success_for_user_id(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + f'/transformations?user_id=user_1', status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 18


def test_GET_transformations_success_for_user_id_empty_result(testapp):
    res = testapp.get(ROUTE_PREFIX + f'/transformations?user_id=test_1', status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 0


def test_POST_transformation_success_dry_run(testapp):
    # Build test request
    json_request = json.dumps({
        'params': {
            'algorithm': 'tps',
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                     {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                     {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                     {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}]
        },
        'map_id': to_public_map_id(10001556),
        'overwrites': 0,
        'user_id': 'test'
    })
    res = testapp.post(ROUTE_PREFIX + '/transformations?dry_run=true', json_request,
                       content_type='application/json; charset=utf-8', status=200)

    assert res.status_int == 200
    assert 'extent' in res.json_body
    assert 'layer_name' in res.json_body
    assert 'wms_url' in res.json_body
    assert 'job_id' not in res.json_body
    assert 'transformation_id' not in res.json_body
    assert 'points' not in res.json_body


def test_POST_transformation_success_dry_run_with_transformation_id(testapp, dbsession):
    # Insert an unprocessed job for the map_id
    map_id = 10001556
    dbsession.add(
        Transformation(
            id=1,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params=json.dumps({'source': 'pixel', 'target': 'EPSG:4314', 'algorithm': 'tps', 'gcps': [
                {'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}
            ]}),
            target_crs=32633,
            validation=EnumValidationValue.INVALID.value,
            raw_map_id=map_id,
            overwrites=0,
            comment=None
        )
    )
    dbsession.flush()

    # Build test request
    json_request = json.dumps({
        'transformation_id': 1,
    })
    res = testapp.post(ROUTE_PREFIX + '/transformations?dry_run=true', json_request,
                       content_type='application/json; charset=utf-8', status=200)

    assert res.status_int == 200
    assert 'extent' in res.json_body
    assert 'layer_name' in res.json_body
    assert 'wms_url' in res.json_body
    assert 'job_id' not in res.json_body
    assert 'transformation_id' not in res.json_body
    assert 'points' not in res.json_body

    dbsession.rollback()

def test_POST_transformation_success_dry_run_with_transformation_id_and_clip(testapp, dbsession):
    # Insert an unprocessed job for the map_id
    map_id = 10001556
    dbsession.add(
        Transformation(
            id=8916,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params=json.dumps({"source": "pixel", "target": "EPSG:4326", "algorithm": "affine", "gcps": [{"source": [4719, 1380], "target": [10.714308619959, 48.755628213793]}, {"source": [2809, 1340], "target": [10.669971704948, 48.755836873379]}, {"source": [1414, 964], "target": [10.636985302208, 48.76146858635]}, {"source": [988, 3018], "target": [10.627818108085, 48.729436326083]}, {"source": [2885, 5235], "target": [10.672315955649, 48.695646899534]}, {"source": [6063, 4201], "target": [10.746548176053, 48.712192253709]}, {"source": [2739, 3238], "target": [10.668661594173, 48.726582481426]}, {"source": [1664, 4171], "target": [10.643736719976, 48.711748022874]}, {"source": [5797, 746], "target": [10.739638209288, 48.765643779367]}, {"source": [6125, 4814], "target": [10.748037099729, 48.70257582834]}]}),
            clip=json.dumps({"type":"Polygon","coordinates":[[[10.620311648,48.764715154],[10.620304942,48.76471869],[10.620310306,48.76471648],[10.747275352,48.765701238],[10.748301744,48.681741906],[10.62171042,48.680702374],[10.621619224,48.680705916],[10.621563495,48.68075816],[10.62159419,48.680721855],[10.620309412,48.764715596],[10.620311648,48.764715154]]]}),
            target_crs=4326,
            validation=EnumValidationValue.VALID.value,
            raw_map_id=map_id,
            overwrites=0,
            comment=None
        )
    )
    dbsession.flush()

    # Build test request
    json_request = json.dumps({
        'transformation_id': 8916,
    })
    res = testapp.post(ROUTE_PREFIX + '/transformations?dry_run=true', json_request,
                       content_type='application/json; charset=utf-8', status=200)

    assert res.status_int == 200
    assert 'extent' in res.json_body
    assert 'layer_name' in res.json_body
    assert 'wms_url' in res.json_body
    assert 'job_id' not in res.json_body
    assert 'transformation_id' not in res.json_body
    assert 'points' not in res.json_body

    dbsession.rollback()

def test_POST_transformation_success_dry_run_with_clip(testapp):
    # Build test request
    json_request = json.dumps({
        'params': {
            'algorithm': 'tps',
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                     {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                     {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                     {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}]},
        'clip': {
            'type': 'Polygon',
            'coordinates': [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974],
                             [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091],
                             [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772],
                             [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
        },
        'map_id': to_public_map_id(10001556),
        'overwrites': 0,
        'user_id': 'test'
    })
    res = testapp.post(ROUTE_PREFIX + '/transformations?dry_run=true', json_request,
                       content_type='application/json; charset=utf-8', status=200)

    assert res.status_int == 200
    assert 'extent' in res.json_body
    assert 'layer_name' in res.json_body
    assert 'wms_url' in res.json_body
    assert 'job_id' not in res.json_body
    assert 'transformation_id' not in res.json_body
    assert 'points' not in res.json_body


def test_POST_transformations_success_new_transformation(testapp, dbsession):
    map_id = 10001558

    # Setup test data
    dbsession.add(
        RawMap(
            id=map_id,
            file_name='df_dk_0010001_3352_191s8',
            enabled=False,
            map_type='M',
            default_crs=4314,
            rel_path='',
            allow_download=False
        )
    )
    dbsession.flush()

    # Create and perform test request
    json_request = {
        'clip': {
            'type': 'Polygon',
            'coordinates': [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974],
                             [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091],
                             [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772],
                             [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
        },
        'params': {
            'algorithm': 'tps',
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                     {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                     {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                     {'source': [6969, 3160], 'target': [14.816612768409, 50.863606051111]},
                     {'source': [1907, 1301], 'target': [14.690521818997, 50.891860483128]},
                     {'source': [4180, 4396], 'target': [14.747856876595, 50.843955582846]},
                     {'source': [5070, 5489], 'target': [14.769772087663, 50.827125251053]},
                     {'source': [6933, 7171], 'target': [14.816342007402, 50.801483295161]},
                     {'source': [3325, 7152], 'target': [14.727274235239, 50.801026963158]},
                     {'source': [1509, 6622], 'target': [14.681454720195, 50.808715847718]},
                     {'source': [2416, 3598], 'target': [14.703546131965, 50.856059148055]},
                     {'source': [7395, 946], 'target': [14.826504192996, 50.898265545769]},
                     {'source': [946, 6862], 'target': [14.666342263936, 50.805188342156]},
                     {'source': [771, 7207], 'target': [14.661734800546, 50.799776765214]},
                     {'source': [7465, 7231], 'target': [14.82938673407, 50.80059467845]},
                     {'source': [788, 781], 'target': [14.663646845572, 50.899831454076]},
                     {'source': [7486, 818], 'target': [14.829132122927, 50.900185560843]},
                     {'source': [7484, 939], 'target': [14.829138205432, 50.898323450806]},
                     {'source': [7483, 1160], 'target': [14.829145688426, 50.894908648825]},
                     {'source': [7478, 2392], 'target': [14.829196331602, 50.874764134307]},
                     {'source': [7471, 3849], 'target': [14.829253978805, 50.852910617897]},
                     {'source': [7465, 6803], 'target': [14.829363593315, 50.80734546335]},
                     {'source': [7464, 5611], 'target': [14.829323125954, 50.825911023952]},
                     {'source': [7072, 816], 'target': [14.818461581754, 50.900162259197]},
                     {'source': [6816, 815], 'target': [14.812297813421, 50.900151361887]},
                     {'source': [6421, 813], 'target': [14.802223053593, 50.900129107788]},
                     {'source': [6618, 814], 'target': [14.807439741575, 50.900140443422]},
                     {'source': [6095, 811], 'target': [14.79396136798, 50.900113591633]},
                     {'source': [5696, 809], 'target': [14.783920384473, 50.900090067859]},
                     {'source': [4628, 802], 'target': [14.75775378559, 50.900032966778]},
                     {'source': [4315, 798], 'target': [14.750505879687, 50.900016164954]},
                     {'source': [4392, 801], 'target': [14.752365899551, 50.900022902391]},
                     {'source': [2144, 787], 'target': [14.696740414531, 50.899902828324]},
                     {'source': [2730, 789], 'target': [14.711380112251, 50.899935584721]},
                     {'source': [1454, 894], 'target': [14.678838241912, 50.898270458088]},
                     {'source': [2110, 787], 'target': [14.695619330344, 50.899901154426]},
                     {'source': [1729, 786], 'target': [14.685688820994, 50.899880165294]},
                     {'source': [788, 1240], 'target': [14.663512309453, 50.892726856692]},
                     {'source': [788, 910], 'target': [14.663606153878, 50.897668380513]},
                     {'source': [786, 2712], 'target': [14.663059846595, 50.869356442866]},
                     {'source': [782, 3878], 'target': [14.662716360693, 50.851226910756]},
                     {'source': [776, 4935], 'target': [14.662403924156, 50.835015826507]},
                     {'source': [775, 6249], 'target': [14.66201809743, 50.814587799125]},
                     {'source': [1129, 7208], 'target': [14.671402656065, 50.799822388914]},
                     {'source': [2847, 7216], 'target': [14.71494617521, 50.80003532242]},
                     {'source': [5029, 7222], 'target': [14.769027444289, 50.800301490166]},
                     {'source': [6878, 7228], 'target': [14.814811178089, 50.800522857232]},
                     {'source': [2344, 5329], 'target': [14.702654426308, 50.828966502252]},
                     {'source': [3227, 5703], 'target': [14.724240369322, 50.823275953506]},
                     {'source': [3401, 5702], 'target': [14.728240875224, 50.823645316122]},
                     {'source': [3564, 6419], 'target': [14.732725721035, 50.812001813382]},
                     {'source': [5055, 6582], 'target': [14.769530816595, 50.809901028317]},
                     {'source': [5040, 6641], 'target': [14.769256299665, 50.808950066353]},
                     {'source': [6587, 5689], 'target': [14.807585452192, 50.824413387287]},
                     {'source': [5454, 6101], 'target': [14.779585654499, 50.817950250277]},
                     {'source': [4307, 6647], 'target': [14.751634272656, 50.808613014558]},
                     {'source': [5574, 7223], 'target': [14.782296084065, 50.800354683619]},
                     {'source': [1354, 784], 'target': [14.67634612815, 50.899859802211]},
                     {'source': [2389, 787], 'target': [14.701935480532, 50.899914589163]},
                     {'source': [3824, 1662], 'target': [14.738689286797, 50.886536375438]},
                     {'source': [3224, 1988], 'target': [14.724086779327, 50.881400957462]},
                     {'source': [5561, 1866], 'target': [14.781628702951, 50.883739028779]},
                     {'source': [4983, 2643], 'target': [14.767642016105, 50.871542857]},
                     {'source': [4726, 2993], 'target': [14.761426208635, 50.866146613586]},
                     {'source': [1752, 2466], 'target': [14.686777727172, 50.873739758153]},
                     {'source': [2120, 3274], 'target': [14.695887327077, 50.860745617059]},
                     {'source': [6153, 3355], 'target': [14.796487598134, 50.860512023302]},
                     {'source': [2581, 6592], 'target': [14.708445231744, 50.809621467831]},
                     {'source': [3009, 3992], 'target': [14.718511063861, 50.849750438399]},
                     {'source': [7188, 7229], 'target': [14.822605684397, 50.800558336973]},
                     {'source': [4111, 3785], 'target': [14.745949775376, 50.85370368877]},
                     {'source': [4006, 3615], 'target': [14.743331660827, 50.856337080476]},
                     {'source': [3893, 3472], 'target': [14.740705479905, 50.858508042521]},
                     {'source': [3737, 4589], 'target': [14.737042129051, 50.840928706352]},
                     {'source': [5695, 4687], 'target': [14.785700030341, 50.840037938729]},
                     {'source': [3367, 793], 'target': [14.727518573288, 50.899969586806]},
                     {'source': [789, 1410], 'target': [14.663452240739, 50.889766853181]},
                     {'source': [783, 3619], 'target': [14.662793178389, 50.855212017021]},
                     {'source': [6387, 7226], 'target': [14.802360083153, 50.800460327448]},
                     {'source': [7467, 4470], 'target': [14.829268312941, 50.843462199227]}]
        },
        'overwrites': 0,
        'user_id': 'test',
        'map_id': to_public_map_id(map_id)
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/transformations', params=json.dumps(json_request),
                       content_type='application/json; charset=utf-8', status=200)

    # First of all rollback session
    dbsession.rollback()

    # Run tests
    assert res.status_int == 200
    assert res.json_body['transformation_id'] != None
    assert res.json_body['job_id'] != None
    assert res.json_body['points'] == 400


def test_POST_transformations_success_new_transformation_multiple_times(testapp, dbsession):
    map_id = 10001558

    # Setup test data
    dbsession.add(
        RawMap(
            id=map_id,
            file_name='df_dk_0010001_3352_191s8',
            enabled=False,
            map_type='M',
            default_crs=4314,
            rel_path='',
            allow_download=False,
        )
    )
    dbsession.flush()

    # Create and perform test request
    params = {
        'clip': {
            'type': 'Polygon',
            'coordinates': [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974],
                             [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091],
                             [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772],
                             [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
        },
        'params': {
            'algorithm': 'tps',
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                     {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                     {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                     {'source': [6969, 3160], 'target': [14.816612768409, 50.863606051111]},
                     {'source': [1907, 1301], 'target': [14.690521818997, 50.891860483128]},
                     {'source': [4180, 4396], 'target': [14.747856876595, 50.843955582846]},
                     {'source': [5070, 5489], 'target': [14.769772087663, 50.827125251053]},
                     {'source': [6933, 7171], 'target': [14.816342007402, 50.801483295161]},
                     {'source': [3325, 7152], 'target': [14.727274235239, 50.801026963158]},
                     {'source': [1509, 6622], 'target': [14.681454720195, 50.808715847718]},
                     {'source': [2416, 3598], 'target': [14.703546131965, 50.856059148055]},
                     {'source': [7395, 946], 'target': [14.826504192996, 50.898265545769]},
                     {'source': [946, 6862], 'target': [14.666342263936, 50.805188342156]},
                     {'source': [771, 7207], 'target': [14.661734800546, 50.799776765214]},
                     {'source': [7465, 7231], 'target': [14.82938673407, 50.80059467845]},
                     {'source': [788, 781], 'target': [14.663646845572, 50.899831454076]},
                     {'source': [7486, 818], 'target': [14.829132122927, 50.900185560843]},
                     {'source': [7484, 939], 'target': [14.829138205432, 50.898323450806]},
                     {'source': [7483, 1160], 'target': [14.829145688426, 50.894908648825]},
                     {'source': [7478, 2392], 'target': [14.829196331602, 50.874764134307]},
                     {'source': [7471, 3849], 'target': [14.829253978805, 50.852910617897]},
                     {'source': [7465, 6803], 'target': [14.829363593315, 50.80734546335]},
                     {'source': [7464, 5611], 'target': [14.829323125954, 50.825911023952]},
                     {'source': [7072, 816], 'target': [14.818461581754, 50.900162259197]},
                     {'source': [6816, 815], 'target': [14.812297813421, 50.900151361887]},
                     {'source': [6421, 813], 'target': [14.802223053593, 50.900129107788]},
                     {'source': [6618, 814], 'target': [14.807439741575, 50.900140443422]},
                     {'source': [6095, 811], 'target': [14.79396136798, 50.900113591633]},
                     {'source': [5696, 809], 'target': [14.783920384473, 50.900090067859]},
                     {'source': [4628, 802], 'target': [14.75775378559, 50.900032966778]},
                     {'source': [4315, 798], 'target': [14.750505879687, 50.900016164954]},
                     {'source': [4392, 801], 'target': [14.752365899551, 50.900022902391]},
                     {'source': [2144, 787], 'target': [14.696740414531, 50.899902828324]},
                     {'source': [2730, 789], 'target': [14.711380112251, 50.899935584721]},
                     {'source': [1454, 894], 'target': [14.678838241912, 50.898270458088]},
                     {'source': [2110, 787], 'target': [14.695619330344, 50.899901154426]},
                     {'source': [1729, 786], 'target': [14.685688820994, 50.899880165294]},
                     {'source': [788, 1240], 'target': [14.663512309453, 50.892726856692]},
                     {'source': [788, 910], 'target': [14.663606153878, 50.897668380513]},
                     {'source': [786, 2712], 'target': [14.663059846595, 50.869356442866]},
                     {'source': [782, 3878], 'target': [14.662716360693, 50.851226910756]},
                     {'source': [776, 4935], 'target': [14.662403924156, 50.835015826507]},
                     {'source': [775, 6249], 'target': [14.66201809743, 50.814587799125]},
                     {'source': [1129, 7208], 'target': [14.671402656065, 50.799822388914]},
                     {'source': [2847, 7216], 'target': [14.71494617521, 50.80003532242]},
                     {'source': [5029, 7222], 'target': [14.769027444289, 50.800301490166]},
                     {'source': [6878, 7228], 'target': [14.814811178089, 50.800522857232]},
                     {'source': [2344, 5329], 'target': [14.702654426308, 50.828966502252]},
                     {'source': [3227, 5703], 'target': [14.724240369322, 50.823275953506]},
                     {'source': [3401, 5702], 'target': [14.728240875224, 50.823645316122]},
                     {'source': [3564, 6419], 'target': [14.732725721035, 50.812001813382]},
                     {'source': [5055, 6582], 'target': [14.769530816595, 50.809901028317]},
                     {'source': [5040, 6641], 'target': [14.769256299665, 50.808950066353]},
                     {'source': [6587, 5689], 'target': [14.807585452192, 50.824413387287]},
                     {'source': [5454, 6101], 'target': [14.779585654499, 50.817950250277]},
                     {'source': [4307, 6647], 'target': [14.751634272656, 50.808613014558]},
                     {'source': [5574, 7223], 'target': [14.782296084065, 50.800354683619]},
                     {'source': [1354, 784], 'target': [14.67634612815, 50.899859802211]},
                     {'source': [2389, 787], 'target': [14.701935480532, 50.899914589163]},
                     {'source': [3824, 1662], 'target': [14.738689286797, 50.886536375438]},
                     {'source': [3224, 1988], 'target': [14.724086779327, 50.881400957462]},
                     {'source': [5561, 1866], 'target': [14.781628702951, 50.883739028779]},
                     {'source': [4983, 2643], 'target': [14.767642016105, 50.871542857]},
                     {'source': [4726, 2993], 'target': [14.761426208635, 50.866146613586]},
                     {'source': [1752, 2466], 'target': [14.686777727172, 50.873739758153]},
                     {'source': [2120, 3274], 'target': [14.695887327077, 50.860745617059]},
                     {'source': [6153, 3355], 'target': [14.796487598134, 50.860512023302]},
                     {'source': [2581, 6592], 'target': [14.708445231744, 50.809621467831]},
                     {'source': [3009, 3992], 'target': [14.718511063861, 50.849750438399]},
                     {'source': [7188, 7229], 'target': [14.822605684397, 50.800558336973]},
                     {'source': [4111, 3785], 'target': [14.745949775376, 50.85370368877]},
                     {'source': [4006, 3615], 'target': [14.743331660827, 50.856337080476]},
                     {'source': [3893, 3472], 'target': [14.740705479905, 50.858508042521]},
                     {'source': [3737, 4589], 'target': [14.737042129051, 50.840928706352]},
                     {'source': [5695, 4687], 'target': [14.785700030341, 50.840037938729]},
                     {'source': [3367, 793], 'target': [14.727518573288, 50.899969586806]},
                     {'source': [789, 1410], 'target': [14.663452240739, 50.889766853181]},
                     {'source': [783, 3619], 'target': [14.662793178389, 50.855212017021]},
                     {'source': [6387, 7226], 'target': [14.802360083153, 50.800460327448]},
                     {'source': [7467, 4470], 'target': [14.829268312941, 50.843462199227]}]
        },
        'overwrites': 0,
        'user_id': 'test',
        'map_id': to_public_map_id(map_id)
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/transformations', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=200)

    # Run tests
    assert res.status_int == 200
    assert res.json_body['transformation_id'] != None
    assert res.json_body['job_id'] != None
    assert res.json_body['points'] == 400

    res = testapp.post(ROUTE_PREFIX + '/transformations', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=400)
    res = testapp.post(ROUTE_PREFIX + '/transformations', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=400)

    assert res.status_int == 400

    # First of all rollback session
    dbsession.rollback()


def test_POST_transformations_success_new_transformation_without_clip(testapp, dbsession):
    map_id = 10001558

    # Setup test data
    dbsession.add(
        RawMap(
            id=map_id,
            file_name='df_dk_0010001_3352_191s8',
            enabled=False,
            map_type='M',
            default_crs=4314,
            rel_path='',
            allow_download=False,
        )
    )
    dbsession.flush()

    # Create and perform test request
    params = {
        'params': {
            'algorithm': 'tps',
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                     {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                     {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                     {'source': [6969, 3160], 'target': [14.816612768409, 50.863606051111]},
                     {'source': [1907, 1301], 'target': [14.690521818997, 50.891860483128]},
                     {'source': [4180, 4396], 'target': [14.747856876595, 50.843955582846]},
                     {'source': [5070, 5489], 'target': [14.769772087663, 50.827125251053]},
                     {'source': [6933, 7171], 'target': [14.816342007402, 50.801483295161]},
                     {'source': [3325, 7152], 'target': [14.727274235239, 50.801026963158]},
                     {'source': [1509, 6622], 'target': [14.681454720195, 50.808715847718]},
                     {'source': [2416, 3598], 'target': [14.703546131965, 50.856059148055]},
                     {'source': [7395, 946], 'target': [14.826504192996, 50.898265545769]},
                     {'source': [946, 6862], 'target': [14.666342263936, 50.805188342156]},
                     {'source': [771, 7207], 'target': [14.661734800546, 50.799776765214]},
                     {'source': [7465, 7231], 'target': [14.82938673407, 50.80059467845]},
                     {'source': [788, 781], 'target': [14.663646845572, 50.899831454076]},
                     {'source': [7486, 818], 'target': [14.829132122927, 50.900185560843]},
                     {'source': [7484, 939], 'target': [14.829138205432, 50.898323450806]},
                     {'source': [7483, 1160], 'target': [14.829145688426, 50.894908648825]},
                     {'source': [7478, 2392], 'target': [14.829196331602, 50.874764134307]},
                     {'source': [7471, 3849], 'target': [14.829253978805, 50.852910617897]},
                     {'source': [7465, 6803], 'target': [14.829363593315, 50.80734546335]},
                     {'source': [7464, 5611], 'target': [14.829323125954, 50.825911023952]},
                     {'source': [7072, 816], 'target': [14.818461581754, 50.900162259197]},
                     {'source': [6816, 815], 'target': [14.812297813421, 50.900151361887]},
                     {'source': [6421, 813], 'target': [14.802223053593, 50.900129107788]},
                     {'source': [6618, 814], 'target': [14.807439741575, 50.900140443422]},
                     {'source': [6095, 811], 'target': [14.79396136798, 50.900113591633]},
                     {'source': [5696, 809], 'target': [14.783920384473, 50.900090067859]},
                     {'source': [4628, 802], 'target': [14.75775378559, 50.900032966778]},
                     {'source': [4315, 798], 'target': [14.750505879687, 50.900016164954]},
                     {'source': [4392, 801], 'target': [14.752365899551, 50.900022902391]},
                     {'source': [2144, 787], 'target': [14.696740414531, 50.899902828324]},
                     {'source': [2730, 789], 'target': [14.711380112251, 50.899935584721]},
                     {'source': [1454, 894], 'target': [14.678838241912, 50.898270458088]},
                     {'source': [2110, 787], 'target': [14.695619330344, 50.899901154426]},
                     {'source': [1729, 786], 'target': [14.685688820994, 50.899880165294]},
                     {'source': [788, 1240], 'target': [14.663512309453, 50.892726856692]},
                     {'source': [788, 910], 'target': [14.663606153878, 50.897668380513]},
                     {'source': [786, 2712], 'target': [14.663059846595, 50.869356442866]},
                     {'source': [782, 3878], 'target': [14.662716360693, 50.851226910756]},
                     {'source': [776, 4935], 'target': [14.662403924156, 50.835015826507]},
                     {'source': [775, 6249], 'target': [14.66201809743, 50.814587799125]},
                     {'source': [1129, 7208], 'target': [14.671402656065, 50.799822388914]},
                     {'source': [2847, 7216], 'target': [14.71494617521, 50.80003532242]},
                     {'source': [5029, 7222], 'target': [14.769027444289, 50.800301490166]},
                     {'source': [6878, 7228], 'target': [14.814811178089, 50.800522857232]},
                     {'source': [2344, 5329], 'target': [14.702654426308, 50.828966502252]},
                     {'source': [3227, 5703], 'target': [14.724240369322, 50.823275953506]},
                     {'source': [3401, 5702], 'target': [14.728240875224, 50.823645316122]},
                     {'source': [3564, 6419], 'target': [14.732725721035, 50.812001813382]},
                     {'source': [5055, 6582], 'target': [14.769530816595, 50.809901028317]},
                     {'source': [5040, 6641], 'target': [14.769256299665, 50.808950066353]},
                     {'source': [6587, 5689], 'target': [14.807585452192, 50.824413387287]},
                     {'source': [5454, 6101], 'target': [14.779585654499, 50.817950250277]},
                     {'source': [4307, 6647], 'target': [14.751634272656, 50.808613014558]},
                     {'source': [5574, 7223], 'target': [14.782296084065, 50.800354683619]},
                     {'source': [1354, 784], 'target': [14.67634612815, 50.899859802211]},
                     {'source': [2389, 787], 'target': [14.701935480532, 50.899914589163]},
                     {'source': [3824, 1662], 'target': [14.738689286797, 50.886536375438]},
                     {'source': [3224, 1988], 'target': [14.724086779327, 50.881400957462]},
                     {'source': [5561, 1866], 'target': [14.781628702951, 50.883739028779]},
                     {'source': [4983, 2643], 'target': [14.767642016105, 50.871542857]},
                     {'source': [4726, 2993], 'target': [14.761426208635, 50.866146613586]},
                     {'source': [1752, 2466], 'target': [14.686777727172, 50.873739758153]},
                     {'source': [2120, 3274], 'target': [14.695887327077, 50.860745617059]},
                     {'source': [6153, 3355], 'target': [14.796487598134, 50.860512023302]},
                     {'source': [2581, 6592], 'target': [14.708445231744, 50.809621467831]},
                     {'source': [3009, 3992], 'target': [14.718511063861, 50.849750438399]},
                     {'source': [7188, 7229], 'target': [14.822605684397, 50.800558336973]},
                     {'source': [4111, 3785], 'target': [14.745949775376, 50.85370368877]},
                     {'source': [4006, 3615], 'target': [14.743331660827, 50.856337080476]},
                     {'source': [3893, 3472], 'target': [14.740705479905, 50.858508042521]},
                     {'source': [3737, 4589], 'target': [14.737042129051, 50.840928706352]},
                     {'source': [5695, 4687], 'target': [14.785700030341, 50.840037938729]},
                     {'source': [3367, 793], 'target': [14.727518573288, 50.899969586806]},
                     {'source': [789, 1410], 'target': [14.663452240739, 50.889766853181]},
                     {'source': [783, 3619], 'target': [14.662793178389, 50.855212017021]},
                     {'source': [6387, 7226], 'target': [14.802360083153, 50.800460327448]},
                     {'source': [7467, 4470], 'target': [14.829268312941, 50.843462199227]}]
        },
        'overwrites': 0,
        'user_id': 'test',
        'map_id': to_public_map_id(map_id)
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/transformations', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=200)

    # First of all rollback session
    dbsession.rollback()

    # Run tests
    assert res.status_int == 200
    assert res.json_body['transformation_id'] != None
    assert res.json_body['job_id'] != None
    assert res.json_body['points'] == 400

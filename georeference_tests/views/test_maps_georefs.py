#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import json
from georeference.models.map import Map
from georeference.settings import ROUTE_PREFIX

def test_getGereofs_success_emptyResult(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10003265

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s/georefs' % map_id, status=200)
    print(res.json)
    assert res.status_int == 200
    assert len(res.json['items']) == 0

def test_getGereofs_success_georefResults(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10001556

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s/georefs' % map_id, status=200)
    assert res.status_int == 200
    assert len(res.json['items']) == 2

def test_postGereofs_success_newGeoref(testapp, dbsession):
    map_id = 10001558

    # Setup test data
    dbsession.add(
        Map(id=map_id, apsobjectid=90015724, apsdateiname='df_dk_0010001_3352_191s8',
            originalimage='', georefimage='', istaktiv=False, isttransformiert=False,
            maptype='M', hasgeorefparams=0, recommendedsrid=4314, image_rel_path='')
    )
    dbsession.flush()

    # Create and perform test request
    params = {
        'clip_polygon': {
            'type': 'Polygon',
            'crs': {'type': 'name', 'properties': {'name': 'EPSG:4314'}},
            'coordinates': [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974], [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091], [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772], [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
        },
        'georef_params': {
            'source': 'pixel',
            'target': 'EPSG:4314',
            'algorithm': 'tps',
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]}, {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]}, {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}, {'source': [6969, 3160], 'target': [14.816612768409, 50.863606051111]}, {'source': [1907, 1301], 'target': [14.690521818997, 50.891860483128]}, {'source': [4180, 4396], 'target': [14.747856876595, 50.843955582846]}, {'source': [5070, 5489], 'target': [14.769772087663, 50.827125251053]}, {'source': [6933, 7171], 'target': [14.816342007402, 50.801483295161]}, {'source': [3325, 7152], 'target': [14.727274235239, 50.801026963158]}, {'source': [1509, 6622], 'target': [14.681454720195, 50.808715847718]}, {'source': [2416, 3598], 'target': [14.703546131965, 50.856059148055]}, {'source': [7395, 946], 'target': [14.826504192996, 50.898265545769]}, {'source': [946, 6862], 'target': [14.666342263936, 50.805188342156]}, {'source': [771, 7207], 'target': [14.661734800546, 50.799776765214]}, {'source': [7465, 7231], 'target': [14.82938673407, 50.80059467845]}, {'source': [788, 781], 'target': [14.663646845572, 50.899831454076]}, {'source': [7486, 818], 'target': [14.829132122927, 50.900185560843]}, {'source': [7484, 939], 'target': [14.829138205432, 50.898323450806]}, {'source': [7483, 1160], 'target': [14.829145688426, 50.894908648825]}, {'source': [7478, 2392], 'target': [14.829196331602, 50.874764134307]}, {'source': [7471, 3849], 'target': [14.829253978805, 50.852910617897]}, {'source': [7465, 6803], 'target': [14.829363593315, 50.80734546335]}, {'source': [7464, 5611], 'target': [14.829323125954, 50.825911023952]}, {'source': [7072, 816], 'target': [14.818461581754, 50.900162259197]}, {'source': [6816, 815], 'target': [14.812297813421, 50.900151361887]}, {'source': [6421, 813], 'target': [14.802223053593, 50.900129107788]}, {'source': [6618, 814], 'target': [14.807439741575, 50.900140443422]}, {'source': [6095, 811], 'target': [14.79396136798, 50.900113591633]}, {'source': [5696, 809], 'target': [14.783920384473, 50.900090067859]}, {'source': [4628, 802], 'target': [14.75775378559, 50.900032966778]}, {'source': [4315, 798], 'target': [14.750505879687, 50.900016164954]}, {'source': [4392, 801], 'target': [14.752365899551, 50.900022902391]}, {'source': [2144, 787], 'target': [14.696740414531, 50.899902828324]}, {'source': [2730, 789], 'target': [14.711380112251, 50.899935584721]}, {'source': [1454, 894], 'target': [14.678838241912, 50.898270458088]}, {'source': [2110, 787], 'target': [14.695619330344, 50.899901154426]}, {'source': [1729, 786], 'target': [14.685688820994, 50.899880165294]}, {'source': [788, 1240], 'target': [14.663512309453, 50.892726856692]}, {'source': [788, 910], 'target': [14.663606153878, 50.897668380513]}, {'source': [786, 2712], 'target': [14.663059846595, 50.869356442866]}, {'source': [782, 3878], 'target': [14.662716360693, 50.851226910756]}, {'source': [776, 4935], 'target': [14.662403924156, 50.835015826507]}, {'source': [775, 6249], 'target': [14.66201809743, 50.814587799125]}, {'source': [1129, 7208], 'target': [14.671402656065, 50.799822388914]}, {'source': [2847, 7216], 'target': [14.71494617521, 50.80003532242]}, {'source': [5029, 7222], 'target': [14.769027444289, 50.800301490166]}, {'source': [6878, 7228], 'target': [14.814811178089, 50.800522857232]}, {'source': [2344, 5329], 'target': [14.702654426308, 50.828966502252]}, {'source': [3227, 5703], 'target': [14.724240369322, 50.823275953506]}, {'source': [3401, 5702], 'target': [14.728240875224, 50.823645316122]}, {'source': [3564, 6419], 'target': [14.732725721035, 50.812001813382]}, {'source': [5055, 6582], 'target': [14.769530816595, 50.809901028317]}, {'source': [5040, 6641], 'target': [14.769256299665, 50.808950066353]}, {'source': [6587, 5689], 'target': [14.807585452192, 50.824413387287]}, {'source': [5454, 6101], 'target': [14.779585654499, 50.817950250277]}, {'source': [4307, 6647], 'target': [14.751634272656, 50.808613014558]}, {'source': [5574, 7223], 'target': [14.782296084065, 50.800354683619]}, {'source': [1354, 784], 'target': [14.67634612815, 50.899859802211]}, {'source': [2389, 787], 'target': [14.701935480532, 50.899914589163]}, {'source': [3824, 1662], 'target': [14.738689286797, 50.886536375438]}, {'source': [3224, 1988], 'target': [14.724086779327, 50.881400957462]}, {'source': [5561, 1866], 'target': [14.781628702951, 50.883739028779]}, {'source': [4983, 2643], 'target': [14.767642016105, 50.871542857]}, {'source': [4726, 2993], 'target': [14.761426208635, 50.866146613586]}, {'source': [1752, 2466], 'target': [14.686777727172, 50.873739758153]}, {'source': [2120, 3274], 'target': [14.695887327077, 50.860745617059]}, {'source': [6153, 3355], 'target': [14.796487598134, 50.860512023302]}, {'source': [2581, 6592], 'target': [14.708445231744, 50.809621467831]}, {'source': [3009, 3992], 'target': [14.718511063861, 50.849750438399]}, {'source': [7188, 7229], 'target': [14.822605684397, 50.800558336973]}, {'source': [4111, 3785], 'target': [14.745949775376, 50.85370368877]}, {'source': [4006, 3615], 'target': [14.743331660827, 50.856337080476]}, {'source': [3893, 3472], 'target': [14.740705479905, 50.858508042521]}, {'source': [3737, 4589], 'target': [14.737042129051, 50.840928706352]}, {'source': [5695, 4687], 'target': [14.785700030341, 50.840037938729]}, {'source': [3367, 793], 'target': [14.727518573288, 50.899969586806]}, {'source': [789, 1410], 'target': [14.663452240739, 50.889766853181]}, {'source': [783, 3619], 'target': [14.662793178389, 50.855212017021]}, {'source': [6387, 7226], 'target': [14.802360083153, 50.800460327448]}, {'source': [7467, 4470], 'target': [14.829268312941, 50.843462199227]}]
        },
        'type': 'new',
        'user_id': 'test'
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/maps/%s/georefs' % map_id, params=json.dumps(params), content_type='application/json; charset=utf-8', status=200)

    # First of all rollback session
    dbsession.rollback()

    # Run tests
    assert res.status_int == 200
    assert res.json_body['id'] != None
    assert res.json_body['points'] == 400







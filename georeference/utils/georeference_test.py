#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import os
import logging
import time

from georeference.utils.georeference import rectify_image_with_clip_and_overviews
from georeference.utils.georeference import rectify_image
from georeference.utils.parser import to_gdal_gcps
from .__testcases_georeference import GEOREFERENCE_TESTCASES

GEOREFERENCE_TESTS = [
    {
        'name': 'Map: test-ak.jpg (11545x9291), Gcps: 4, Algorithm: Polynom, Without clip polygon',
        'algorithm': 'polynom',
        'clip': None,
        'gcps': [{'source': [5473, 6079], 'target': [13.322571166912697, 50.869534359847236]},
                 {'source': [5670, 5589], 'target': [13.346566162286086, 50.91926655702792]},
                 {'source': [7020, 6807], 'target': [13.53735995082988, 50.802610870942374]},
                 {'source': [7812, 5913], 'target': [13.667546305614797, 50.89755275702876]}],
        'srcFile': '../__test_data/data_input/test-ak.jpg',
        'srs': 'EPSG:4314',
    },
    {
        'name': 'Map: df_dk_0010001_5154_1892.tif (8250x9294), Gcps: >80, Algorithm: tps, Without clip polygon',
        'algorithm': 'tps',
        'clip': {"type": "Polygon", "crs": {"type": "name", "properties": {"name": "EPSG:4314"}}, "coordinates": [
            [[14.663647152, 50.899831878], [14.661734496, 50.799776766], [14.764825271, 50.800276975],
             [14.766010982, 50.800290519], [14.766134478, 50.790482956], [14.782466163, 50.790564092],
             [14.782294868, 50.800358076], [14.829388686, 50.80059468], [14.829132978, 50.900185774],
             [14.829130296, 50.900185774], [14.663647152, 50.899831878]]]},
        'gcps': [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]},
                 {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]},
                 {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]},
                 {"source": [6969, 3160], "target": [14.816612768409, 50.863606051111]},
                 {"source": [1907, 1301], "target": [14.690521818997, 50.891860483128]},
                 {"source": [4180, 4396], "target": [14.747856876595, 50.843955582846]},
                 {"source": [5070, 5489], "target": [14.769772087663, 50.827125251053]},
                 {"source": [6933, 7171], "target": [14.816342007402, 50.801483295161]},
                 {"source": [3325, 7152], "target": [14.727274235239, 50.801026963158]},
                 {"source": [1509, 6622], "target": [14.681454720195, 50.808715847718]},
                 {"source": [2416, 3598], "target": [14.703546131965, 50.856059148055]},
                 {"source": [7395, 946], "target": [14.826504192996, 50.898265545769]},
                 {"source": [946, 6862], "target": [14.666342263936, 50.805188342156]},
                 {"source": [771, 7207], "target": [14.661734800546, 50.799776765214]},
                 {"source": [7465, 7231], "target": [14.82938673407, 50.80059467845]},
                 {"source": [788, 781], "target": [14.663646845572, 50.899831454076]},
                 {"source": [7486, 818], "target": [14.829132122927, 50.900185560843]}],
        'srcFile': '../__test_data/data_input/df_dk_0010001_5154_1892.tif',
        'srs': 'EPSG:4314',
    },
]

# Directory which to use as temporary or output dir for tests
TMP_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../__test_data/data_output')


# @pytest.mark.skip(reason="Needs to long")
def test_rectify_image():
    testcases = GEOREFERENCE_TESTCASES + GEOREFERENCE_TESTS
    t0 = time.time()
    print('Test %s georeference test cases' % len(testcases))
    for test in testcases:
        algorithm = test['algorithm']
        srs = test['srs']
        src_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), test['srcFile'])
        if os.path.exists(src_file):
            tmp_dir = os.path.realpath(TMP_DIR)
            dst_file = os.path.join(
                tmp_dir,
                '%s_espg:%s_gcps:%s_%s.tif' % (
                    os.path.splitext(os.path.basename(test['srcFile']))[0],
                    test['srs'],
                    len(test['gcps']),
                    algorithm
                )
            )
            gcps = to_gdal_gcps(test['gcps'])

            t00 = time.time()
            response = rectify_image(src_file, dst_file, algorithm, gcps, srs, logging, tmp_dir, None)
            print('Test: %s (Time: %s)' % (test['name'], (time.time()) - t00))

            # Tests
            assert os.path.exists(response)
            assert response == dst_file
        else:
            print('Skip test case: %s' % test['name'])

    print('Executed %s tests (Time: %s)' % (len(testcases), (time.time()) - t0))


# @pytest.mark.skip(reason="Needs to long")
def test_rectify_image_with_clip_and_overviews():
    testcases = list(filter(lambda g: g['clip'] != None, GEOREFERENCE_TESTCASES))
    t0 = time.time()
    print('Test %s georeference (full) test cases' % len(testcases))
    for test in testcases:
        algorithm = test['algorithm']
        gcps_srs = test['srs']
        clip = test['clip']
        src_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), test['srcFile'])
        if os.path.exists(src_file):
            tmp_dir = os.path.realpath(TMP_DIR)
            dst_file = os.path.join(
                tmp_dir,
                '%s_%s_gcps:%s_%s_clip.tif' % (
                    os.path.splitext(os.path.basename(test['srcFile']))[0],
                    test['srs'],
                    len(test['gcps']),
                    algorithm
                )
            )
            gcps = to_gdal_gcps(test['gcps'])

            t00 = time.time()
            response = rectify_image_with_clip_and_overviews(
                src_file,
                dst_file,
                algorithm,
                gcps,
                gcps_srs,
                logging,
                tmp_dir,
                clip,
            )
            print('Test: %s (Time: %s)' % (test['name'], (time.time()) - t00))

            # Tests
            assert os.path.exists(response)
            assert response == dst_file
        else:
            print('Skip test case: %s' % test['name'])

    print('Executed %s tests (Time: %s)' % (len(testcases), (time.time()) - t0))

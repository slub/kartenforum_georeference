#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import os
import logging
import time
from osgeo import gdal
from georeference.utils.georeference import rectifyImage
from georeference.utils.parser import toGDALGcps
from .testcases_georeference import GEOREFERENCE_TESTCASES

GEOREFERENCE_TESTS = [
    {
        'name': 'Map: test-ak.jpg (11545x9291), Gcps: 4, Algorithm: Polynom, Without clip polygon',
        'algorithm': 'polynom',
        'clip': None,
        'gcps': [{'source': [5473, 6079], 'target': [13.322571166912697, 50.869534359847236]},
                 {'source': [5670, 5589], 'target': [13.346566162286086, 50.91926655702792]},
                 {'source': [7020, 6807], 'target': [13.53735995082988, 50.802610870942374]},
                 {'source': [7812, 5913], 'target': [13.667546305614797, 50.89755275702876]}],
        'srcFile': '../data_input/test-ak.jpg',
        'srs': 4314,
    }
]

# Directory which to use as temporary or output dir for tests
TMP_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data_output')

def test_georeference():
    testcases = GEOREFERENCE_TESTCASES + GEOREFERENCE_TESTS
    t0 = time.time()
    print('Test %s georeference test cases' % len(testcases))
    for test in testcases:
        algorithm = test['algorithm']
        srs = test['srs']
        srcFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), test['srcFile'])
        if os.path.exists(srcFile):
            tmpDir = os.path.realpath(TMP_DIR)
            dstFile = os.path.join(
                tmpDir,
                '%s_espg:%s_gcps:%s_%s.tif' % (
                    os.path.splitext(os.path.basename(test['srcFile']))[0],
                    test['srs'],
                    len(test['gcps']),
                    algorithm
                )
            )
            gcps = toGDALGcps(test['gcps'])

            t00 = time.time()
            response = rectifyImage(srcFile, dstFile, algorithm, gcps, srs, logging, tmpDir, None)
            print('Test: %s (Time: %s)' % (test['name'], (time.time()) - t00))

            # Tests
            assert os.path.exists(response)
            assert response == dstFile
        else:
            print('Skip test case: %s' % test['name'])

    print('Executed %s tests (Time: %s)' % (len(testcases), (time.time()) - t0))
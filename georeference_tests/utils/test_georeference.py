#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import logging
import time
from osgeo import gdal
from georeference.utils.georeference import rectifyPolynomWithVRT

GEOREFERENCE_TESTS = [
    {
        'name': 'Map: test-ak.jpg (11545x9291), Gcps: 13, Algorithm: Polynom',
        'algorithm': 'polynom',
        'gcps': [
            (13.322571166912697, 50.869534359847236, 5473, 6079),
            (13.346566162286086, 50.91926655702792, 5670, 5589),
            (13.53735995082988, 50.802610870942374, 7020, 6807),
            (13.667546305614797, 50.89755275702876, 7812, 5913),
            (13.741126714401176, 51.05625639529854, 8338, 4161),
            (13.681169234684086, 51.1685499300691, 7942, 2791),
            (13.47756543137287, 51.16569220735402, 6609, 2882),
            (13.300067220165836, 51.06061124738151, 5102, 4096),
            (13.310932518222272, 51.19680951127774, 5295, 2447),
            (12.921352950966174, 50.83419856543994, 2536, 6561),
            (12.983108161200633, 50.984707383627985, 3048, 5009),
            (12.973153769483801, 51.099562229978154, 3091, 3676),
            (13.119775225375355, 51.12445831286638, 4017, 3228),
            (13.124513229340627, 50.97154471762153, 4037, 4961),
        ],
        'srcFile': '../data_input/test-ak.jpg',
        'srs': 4314,
    }
]

# Directory which to use as temporary or output dir for tests
TMP_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data_output')

def test_georeference():
    for test in GEOREFERENCE_TESTS:
        algorithm = test['algorithm']
        srs = test['srs']
        srcFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), test['srcFile'])
        tmpDir = os.path.realpath(TMP_DIR)
        dstFile = os.path.join(
            tmpDir,
            '%s_espg:%s_%s.tif' % (
                os.path.splitext(os.path.basename(test['srcFile']))[0],
                test['srs'],
                algorithm
            )
        )
        gcps = list(map(lambda gcp: gdal.GCP(gcp[0], gcp[1], 0, gcp[2], gcp[3]), test['gcps']))

        t0 = time.time()
        response = None
        if algorithm == 'polynom':
            response = rectifyPolynomWithVRT(srcFile, dstFile, gcps, srs, logging, tmpDir, None, order=1)

        # Tests
        assert os.path.exists(response)
        assert response == dstFile

        print('%s (Time: %s)' % (test['name'], (time.time()) - t0))
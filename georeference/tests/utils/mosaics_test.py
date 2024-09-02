#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 22.06.22
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import shutil
import json
import os
from datetime import datetime

from loguru import logger

from georeference.config.paths import PATH_TMP_ROOT, PATH_IMAGE_ROOT
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.models.transformation import Transformation, EnumValidationValue
from georeference.utils.mosaics import create_mosaic_dataset, create_mosaic_overviews


def test_create_mosaic_dataset():
    try:
        # Setup the test data. This also contains the process of creating test georeference images.
        tmp_dir = os.path.join(
            PATH_TMP_ROOT,
            "test_create_mosaic_dataset",
        )
        test_data_georef_images = _create_test_data(tmp_dir)

        # Create the mosaic dataset
        test_dataset = create_mosaic_dataset(
            dataset_name="test_create_mosaic_dataset",
            target_dir=tmp_dir,
            geo_images=test_data_georef_images,
            target_crs=3857,
        )
        assert test_dataset is not None
        assert os.path.exists(test_dataset)

        # Test also creation of overviews
        test_dataset_overviews = create_mosaic_overviews(
            target_dataset=test_dataset, overview_levels="2"
        )
        logger.debug(test_dataset_overviews)
        assert test_dataset_overviews is not None
        assert os.path.exists(test_dataset_overviews)

    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)


def _create_test_data(tmp_dir):
    test_data = [
        {
            "raw_map_id": 11823,
            "transformation_id": 11823,
            "file_name": "df_dk_0010001_5154_1892",
            "params": {
                "source": "pixel",
                "target": "EPSG:4314",
                "algorithm": "tps",
                "gcps": [
                    {
                        "source": [720.8952, 107.3811],
                        "target": [14.809598142072, 50.897193140898],
                    },
                    {
                        "source": [716.1610, 101.5709],
                        "target": [14.808447338463, 50.898010359738],
                    },
                    {
                        "source": [82.9567, 775.4465],
                        "target": [14.661734800546, 50.799776765214],
                    },
                    {
                        "source": [346.8905, 213.9014],
                        "target": [14.724086779327, 50.881400957462],
                    },
                    {
                        "source": [687.2176, 777.4909],
                        "target": [14.802360083153, 50.800460327448],
                    },
                    {
                        "source": [803.4216, 480.9555],
                        "target": [14.829268312941, 50.843462199227],
                    },
                ],
            },
            "target_crs": 4134,
            "clip": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [14.661738422, 50.898624488],
                        [14.659828457, 50.798581177],
                        [14.762903562, 50.799082323],
                        [14.764089092, 50.799095878],
                        [14.764212808, 50.789289473],
                        [14.78054201, 50.789370759],
                        [14.780370504, 50.799163585],
                        [14.827457164, 50.799400622],
                        [14.827199053, 50.898979951],
                        [14.827196371, 50.898979951],
                        [14.661738422, 50.898624488],
                    ]
                ],
            },
        },
        {
            "raw_map_id": 10001963,
            "transformation_id": 12347,
            "file_name": "df_dk_0010001_4948_1925",
            "params": {
                "source": "pixel",
                "target": "EPSG:4326",
                "algorithm": "tps",
                "gcps": [
                    {
                        "source": [64.5056, 781.4888],
                        "target": [13.666666027017, 50.99999999723],
                    },
                    {
                        "source": [64.0690, 74.4379],
                        "target": [13.666666026815, 51.100002285881],
                    },
                    {
                        "source": [806.9199, 74.0013],
                        "target": [13.833333964808, 51.100002285758],
                    },
                    {
                        "source": [807.1382, 780.2881],
                        "target": [13.833333965012, 50.999999997108],
                    },
                    {
                        "source": [785.0906, 86.1166],
                        "target": [13.828561348891, 51.098331952453],
                    },
                    {
                        "source": [388.7797, 349.2687],
                        "target": [13.73942780974, 51.061101729711],
                    },
                    {
                        "source": [685.3307, 479.1530],
                        "target": [13.805931843907, 51.042758774578],
                    },
                ],
            },
            "target_crs": 4326,
            "clip": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [13.664908318, 51.098762208],
                        [13.664907556, 50.998767139],
                        [13.831549483, 50.998774791],
                        [13.831545998, 51.098763835],
                        [13.664908318, 51.098762208],
                    ]
                ],
            },
        },
        {
            "raw_map_id": 10007521,
            "transformation_id": 12187,
            "file_name": "df_dk_0010002_0004",
            "params": {
                "source": "pixel",
                "target": "EPSG:4326",
                "algorithm": "tps",
                "gcps": [
                    {
                        "source": [331.9825, 414.1729],
                        "target": [14.423772091223, 51.182450164502],
                    },
                    {
                        "source": [542.7057, 524.5220],
                        "target": [14.667069906319, 51.100342060004],
                    },
                    {
                        "source": [821.5919, 431.1097],
                        "target": [14.992153638221, 51.158353878838],
                    },
                    {
                        "source": [173.0050, 137.2610],
                        "target": [14.244788283506, 51.385736107192],
                    },
                    {
                        "source": [110.7648, 108.7905],
                        "target": [14.174072089556, 51.407410074107],
                    },
                    {
                        "source": [107.3358, 767.0407],
                        "target": [14.16269562121, 50.925630625192],
                    },
                    {
                        "source": [771.4048, 629.1563],
                        "target": [14.93029117575, 51.018361521668],
                    },
                    {
                        "source": [609.1022, 768.1837],
                        "target": [14.743035433885, 50.920959891845],
                    },
                    {
                        "source": [609.8296, 636.6376],
                        "target": [14.743770359086, 51.015772824239],
                    },
                    {
                        "source": [877.7016, 307.5644],
                        "target": [15.061469434251, 51.249775568628],
                    },
                    {
                        "source": [876.1430, 536.0557],
                        "target": [15.054846524671, 51.081113959285],
                    },
                    {
                        "source": [875.7273, 622.8180],
                        "target": [15.05240142141, 51.018817459452],
                    },
                    {
                        "source": [121.1554, 488.6741],
                        "target": [14.179809093475, 51.127778830973],
                    },
                    {
                        "source": [532.0033, 390.5860],
                        "target": [14.658204675507, 51.197063252325],
                    },
                ],
            },
            "target_crs": 4326,
            "clip": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [14.172958726, 51.407210516],
                        [15.067182551, 51.394760874],
                        [15.048491738, 50.91846162],
                        [14.163202816, 50.925701945],
                        [14.172958726, 51.407210516],
                    ]
                ],
            },
        },
    ]

    # Create georeference images for the given test_data
    georef_images = []
    for d in test_data:
        f = d["file_name"]
        georef_images.append(
            run_process_geo_image(
                Transformation(
                    id=10000001,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    params=json.dumps(d["params"]),
                    validation=EnumValidationValue.MISSING.value,
                    raw_map_id=d["raw_map_id"],
                    overwrites=0,
                    comment=None,
                    clip=json.dumps(d["clip"]),
                ),
                os.path.abspath(os.path.join(PATH_IMAGE_ROOT, f"./{f}.tif")),
                os.path.join(tmp_dir, f"{f}_mosaics_tests.tif"),
            )
        )

    return georef_images

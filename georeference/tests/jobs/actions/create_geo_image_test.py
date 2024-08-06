#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os
from datetime import datetime

from georeference.config.paths import BASE_PATH
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.models.transformation import Transformation, EnumValidationValue


def create_test_data(test_name):
    return {
        "transformationObj": Transformation(
            id=10000001,
            submitted=datetime.now().isoformat(),
            user_id="test",
            params=json.dumps(
                {
                    "source": "pixel",
                    "target": "EPSG:4314",
                    "algorithm": "affine",
                    "gcps": [
                        {
                            "source": [6700, 998],
                            "target": [14.809598142072, 50.897193140898],
                        },
                        {
                            "source": [6656, 944],
                            "target": [14.808447338463, 50.898010359738],
                        },
                        {
                            "source": [6687, 1160],
                            "target": [14.809553411787, 50.894672081543],
                        },
                        {
                            "source": [6969, 3160],
                            "target": [14.816612768409, 50.863606051111],
                        },
                        {
                            "source": [1907, 1301],
                            "target": [14.690521818997, 50.891860483128],
                        },
                        {
                            "source": [4180, 4396],
                            "target": [14.747856876595, 50.843955582846],
                        },
                        {
                            "source": [5070, 5489],
                            "target": [14.769772087663, 50.827125251053],
                        },
                        {
                            "source": [6933, 7171],
                            "target": [14.816342007402, 50.801483295161],
                        },
                        {
                            "source": [3325, 7152],
                            "target": [14.727274235239, 50.801026963158],
                        },
                        {
                            "source": [1509, 6622],
                            "target": [14.681454720195, 50.808715847718],
                        },
                        {
                            "source": [2416, 3598],
                            "target": [14.703546131965, 50.856059148055],
                        },
                        {
                            "source": [7395, 946],
                            "target": [14.826504192996, 50.898265545769],
                        },
                        {
                            "source": [946, 6862],
                            "target": [14.666342263936, 50.805188342156],
                        },
                        {
                            "source": [771, 7207],
                            "target": [14.661734800546, 50.799776765214],
                        },
                        {
                            "source": [7465, 7231],
                            "target": [14.82938673407, 50.80059467845],
                        },
                        {
                            "source": [788, 781],
                            "target": [14.663646845572, 50.899831454076],
                        },
                        {
                            "source": [7486, 818],
                            "target": [14.829132122927, 50.900185560843],
                        },
                    ],
                }
            ),
            validation=EnumValidationValue.MISSING.value,
            raw_map_id=10010367,
            overwrites=0,
            comment=None,
            clip=json.dumps(
                {
                    "type": "Polygon",
                    "crs": {"type": "name", "properties": {"name": "EPSG:4314"}},
                    "coordinates": [
                        [
                            [14.663647152, 50.899831878],
                            [14.661734496, 50.799776766],
                            [14.764825271, 50.800276975],
                            [14.766010982, 50.800290519],
                            [14.766134478, 50.790482956],
                            [14.782466163, 50.790564092],
                            [14.782294868, 50.800358076],
                            [14.829388686, 50.80059468],
                            [14.829132978, 50.900185774],
                            [14.829130296, 50.900185774],
                            [14.663647152, 50.899831878],
                        ]
                    ],
                }
            ),
        ),
        "srcPath": os.path.join(
            BASE_PATH,
            "__test_data/data_input/df_dk_0010001_5154_1892.tif",
        ),
        "trgPath": os.path.join(
            BASE_PATH,
            "__test_data/data_output/test_%s.tif" % test_name,
        ),
    }


def test_run_process_geo_image_success():
    """The proper working of the action for processing geo images."""
    try:
        # Perform the test
        test_data = create_test_data("test_runProcessGeoImage_success")
        subject = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )

        assert os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)


def test_run_process_geo_image_force_success():
    """The proper working of the action for processing geo images."""
    try:
        # Initial create the process
        test_data = create_test_data("test_runProcessGeoImage_force_success")
        subject = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )
        first_modification_time = os.path.getmtime(subject)

        # If "runProcessGeoImage" is run a second time and the image already exists, the functions
        # skips the processing. We can check this by comparing modifications times
        subject = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )
        second_modification_time = os.path.getmtime(subject)

        # If "runProcessGeoImage" is run a third time and the image already exists, we use the "force" parameter
        # to overwrite a existing image. We can check this by comparing modifications times
        subject = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
            force=True,
        )
        third_modification_time = os.path.getmtime(subject)

        assert first_modification_time == second_modification_time
        assert first_modification_time != third_modification_time
    finally:
        if os.path.exists(subject):
            os.remove(subject)

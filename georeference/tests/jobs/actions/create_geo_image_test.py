#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os
from datetime import datetime

from georeference.config.paths import PATH_IMAGE_ROOT, PATH_TMP_ROOT
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.models.transformation import Transformation, EnumValidationValue


def create_test_data(
    test_name: str,
    file_name: str = "df_dk_0010001_5154_1892",
    target_epsg: str = "EPSG:4314",
):
    return {
        "transformationObj": Transformation(
            id=10000001,
            submitted=datetime.now().isoformat(),
            user_id="test",
            params=json.dumps(
                {
                    "source": "pixel",
                    "target": target_epsg,
                    "algorithm": "affine",
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
                            "source": [719.4964, 124.8117],
                            "target": [14.809553411787, 50.894672081543],
                        },
                        {
                            "source": [749.8386, 340.0043],
                            "target": [14.816612768409, 50.863606051111],
                        },
                        {
                            "source": [205.1861, 139.9828],
                            "target": [14.690521818997, 50.891860483128],
                        },
                        {
                            "source": [449.7525, 472.9933],
                            "target": [14.747856876595, 50.843955582846],
                        },
                        {
                            "source": [545.5132, 590.5961],
                            "target": [14.769772087663, 50.827125251053],
                        },
                        {
                            "source": [745.9651, 771.5731],
                            "target": [14.816342007402, 50.801483295161],
                        },
                        {
                            "source": [357.7577, 769.5287],
                            "target": [14.727274235239, 50.801026963158],
                        },
                        {
                            "source": [162.3628, 712.5027],
                            "target": [14.681454720195, 50.808715847718],
                        },
                        {
                            "source": [259.9527, 387.1315],
                            "target": [14.703546131965, 50.856059148055],
                        },
                        {
                            "source": [795.6746, 101.7861],
                            "target": [14.826504192996, 50.898265545769],
                        },
                        {
                            "source": [101.7861, 738.3258],
                            "target": [14.666342263936, 50.805188342156],
                        },
                        {
                            "source": [82.9567, 775.4465],
                            "target": [14.661734800546, 50.799776765214],
                        },
                        {
                            "source": [803.2064, 778.0288],
                            "target": [14.82938673407, 50.80059467845],
                        },
                        {
                            "source": [84.7859, 84.0327],
                            "target": [14.663646845572, 50.899831454076],
                        },
                        {
                            "source": [805.4659, 88.0138],
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
        "srcPath": os.path.abspath(os.path.join(PATH_IMAGE_ROOT, f"./{file_name}.tif")),
        "trgPath": os.path.abspath(
            os.path.join(PATH_TMP_ROOT, f"./test_{test_name}.tif")
        ),
    }


def test_run_process_geo_image_success():
    """The proper working of the action for processing geo images."""
    try:
        # Perform the test
        test_data = create_test_data("test_runProcessGeoImage_success")
        print(test_data)
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 26.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from datetime import datetime

import pytest
from sqlmodel import Session, select

from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation, EnumValidationValue
from georeference.utils.parser import to_public_map_id


@pytest.mark.user("test")
class TestTransformationGet:
    def test_get_transformations_for_map_id_success(
        self,
        test_client,
        override_get_session,
        db_container,
        override_get_user_from_session,
    ):
        map_id = 10001556

        with Session(db_container[1]) as session:
            # Insert an unprocessed job for the map_id
            session.add(
                Transformation(
                    id=1,
                    submitted=datetime.now(),
                    user_id="test",
                    params=json.dumps(
                        {
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
                                    "source": [719.4964, 124.8117],
                                    "target": [14.809553411787, 50.894672081543],
                                },
                                {
                                    "source": [719.4964, 124.8117],
                                    "target": [14.809553411787, 50.894672081543],
                                },
                            ],
                        }
                    ),
                    clip=json.dumps(
                        {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [13.71812582, 51.074800786],
                                    [13.709993362, 51.060460491],
                                    [13.703641892, 51.049528679],
                                    [13.751320839, 51.038047836],
                                    [13.76591742, 51.063727394],
                                    [13.749228716, 51.067503095],
                                    [13.71812582, 51.074800786],
                                ]
                            ],
                            "crs": {
                                "type": "name",
                                "properties": {"name": "EPSG:4314"},
                            },
                        }
                    ),
                    target_crs=4314,
                    validation=EnumValidationValue.MISSING.value,
                    raw_map_id=10001556,
                    overwrites=0,
                    comment=None,
                )
            )
            session.add(
                Job(
                    id=1,
                    submitted=datetime.now(),
                    user_id="test",
                    type=EnumJobType.TRANSFORMATION_PROCESS.value,
                    description='{ "transformation_id": 1 }',
                    state=EnumJobState.NOT_STARTED.value,
                )
            )
            session.commit()

            res = session.exec(
                select(Transformation).where(Transformation.raw_map_id == map_id)
            ).all()
            assert len(res) == 5

        # Build test request
        res = test_client.get(
            f"/transformations?map_id={to_public_map_id(map_id)}&additional_properties=true"
        )
        assert res.status_code == 200
        result = res.json()

        assert len(result["transformations"]) == 5
        assert result["additional_properties"]["pending_jobs"]

        # Check proper transformation of the target_crs
        transformation_subject = result["transformations"][0]
        assert transformation_subject["params"]["target"] == "EPSG:4326"
        assert len(transformation_subject["params"]["gcps"]) == 4
        assert round(
            transformation_subject["params"]["gcps"][0]["target"][0], 6
        ) == round(14.807667264759935, 6)
        assert round(
            transformation_subject["params"]["gcps"][0]["target"][1], 6
        ) == round(50.89598748103341, 6)

        print(transformation_subject["clip"])
        # Check proper coordinate system of the clip polygon
        assert (
            transformation_subject["clip"]["crs"]["properties"]["name"] == "EPSG:4326"
        )

    def test_get_transformations_for_map_id_success_empty_result(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        # Build test request
        res = test_client.get(
            f"/transformations?map_id={to_public_map_id(10003265)}&additional_properties=true"
        )
        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 0

    def test_get_transformations_for_map_id_success_two_results(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        # Build test request
        res = test_client.get(
            f"/transformations?map_id={to_public_map_id(10009466)}&additional_properties=true"
        )
        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 2

    def test_get_transformations_for_map_id_success_transformations_only_invalid(
        self,
        test_client,
        override_get_session,
        db_container,
        override_get_user_from_session,
    ):
        map_id = 10001556

        # Insert an unprocessed job for the map_id
        with Session(db_container[1]) as session:
            session.add(
                Transformation(
                    id=1,
                    submitted=datetime.now(),
                    user_id="test",
                    params=json.dumps(
                        {
                            "source": "pixel",
                            "target": "EPSG:4314",
                            "algorithm": "tps",
                            "gcps": [],
                        }
                    ),
                    target_crs=4314,
                    validation=EnumValidationValue.INVALID.value,
                    raw_map_id=map_id,
                    overwrites=0,
                    comment=None,
                    clip=json.dumps(
                        {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [13.71812582, 51.074800786],
                                    [13.709993362, 51.060460491],
                                    [13.703641892, 51.049528679],
                                    [13.751320839, 51.038047836],
                                    [13.76591742, 51.063727394],
                                    [13.749228716, 51.067503095],
                                    [13.71812582, 51.074800786],
                                ]
                            ],
                            "crs": {
                                "type": "name",
                                "properties": {"name": "EPSG:4314"},
                            },
                        }
                    ),
                )
            )
            session.add(
                Job(
                    id=1,
                    submitted=datetime.now(),
                    user_id="test",
                    type=EnumJobType.TRANSFORMATION_PROCESS.value,
                    description='{ "transformation_id": 1 }',
                    state=EnumJobState.NOT_STARTED.value,
                )
            )
            session.commit()

        # Build test request
        res = test_client.get(
            f"/transformations?map_id={to_public_map_id(map_id)}&additional_properties=false&validation={EnumValidationValue.INVALID.value}",
        )
        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 1
        assert "additional_properties" not in result

    def test_get_transformations_success_for_validation_state_empty_result(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.get("/transformations?validation=test")
        assert res.status_code == 422

    def test_get_transformations_success_for_validation_state_missing(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.get(
            f"/transformations?validation={EnumValidationValue.MISSING.value}",
        )
        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 4

    def test_get_transformations_success_for_validation_state_valid(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.get(
            f"/transformations?validation={EnumValidationValue.VALID.value}",
        )

        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 17

    def test_get_transformations_success_for_validation_state_invalid(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.get(
            f"/transformations?validation={EnumValidationValue.INVALID.value}"
        )
        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 2

    def test_get_transformations_success_for_user_id(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.get("/transformations?user_id=user_1")
        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 18

    def test_get_transformations_success_for_user_id_empty_result(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.get("/transformations?user_id=test_1")
        assert res.status_code == 200
        result = res.json()
        assert len(result["transformations"]) == 0


@pytest.mark.user("test")
class TestTransformationPost:
    def test_post_transformation_success_dry_run(
        self, test_client, override_get_session, override_get_user_from_session
    ):
        # Build test request
        json_request = json.dumps(
            {
                "params": {
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
                            "source": [719.4964, 124.8117],
                            "target": [14.809553411787, 50.894672081543],
                        },
                        {
                            "source": [719.4964, 124.8117],
                            "target": [14.809553411787, 50.894672081543],
                        },
                    ],
                },
                "map_id": to_public_map_id(10001556),
                "overwrites": 0,
            }
        )

        res = test_client.post(
            "/transformations?dry_run=true",
            data=json_request,
        )

        assert res.status_code == 200
        result = res.json()
        assert "extent" in result
        assert "layer_name" in result
        assert "wms_url" in result
        assert "job_id" not in result
        assert "transformation_id" not in result
        assert "points" not in result

    def test_post_transformation_success_dry_run_with_transformation_id(
        self,
        test_client,
        db_container,
        override_get_session,
        override_get_user_from_session,
    ):
        # Insert an unprocessed job for the map_id
        map_id = 10001556
        with Session(db_container[1]) as session:
            session.add(
                Transformation(
                    id=1,
                    submitted=datetime.now(),
                    user_id="test",
                    params=json.dumps(
                        {
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
                                    "source": [719.4964, 124.8117],
                                    "target": [14.809553411787, 50.894672081543],
                                },
                                {
                                    "source": [719.4964, 124.8117],
                                    "target": [14.809553411787, 50.894672081543],
                                },
                            ],
                        }
                    ),
                    target_crs=32633,
                    validation=EnumValidationValue.INVALID.value,
                    raw_map_id=map_id,
                    overwrites=0,
                    comment=None,
                )
            )
            session.commit()

            assert (
                len(
                    session.exec(
                        select(Transformation).where(Transformation.id == 1)
                    ).all()
                )
                == 1
            )

        # Build test request
        json_request = json.dumps(
            {
                "transformation_id": 1,
            }
        )
        res = test_client.post(
            "/transformations?dry_run=true",
            data=json_request,
        )

        assert res.status_code == 200
        result = res.json()
        assert "extent" in result
        assert "layer_name" in result
        assert "wms_url" in result
        assert "job_id" not in result
        assert "transformation_id" not in result
        assert "points" not in result

    def test_post_transformation_success_dry_run_with_transformation_id_and_clip(
        self,
        test_client,
        db_container,
        override_get_session,
        override_get_user_from_session,
    ):
        # Insert an unprocessed job for the map_id
        map_id = 10001556
        with Session(db_container[1]) as session:
            session.add(
                Transformation(
                    id=8916,
                    submitted=datetime.now(),
                    user_id="test",
                    params=json.dumps(
                        {
                            "source": "pixel",
                            "target": "EPSG:4326",
                            "algorithm": "affine",
                            "gcps": [
                                {
                                    "source": [507.7469, 148.4829],
                                    "target": [10.714308619959, 48.755628213793],
                                },
                                {
                                    "source": [302.2380, 144.1790],
                                    "target": [10.669971704948, 48.755836873379],
                                },
                                {
                                    "source": [152.1412, 103.7228],
                                    "target": [10.636985302208, 48.76146858635],
                                },
                                {
                                    "source": [106.3051, 324.7256],
                                    "target": [10.627818108085, 48.729436326083],
                                },
                                {
                                    "source": [310.4153, 563.2666],
                                    "target": [10.672315955649, 48.695646899534],
                                },
                                {
                                    "source": [652.3564, 452.0121],
                                    "target": [10.746548176053, 48.712192253709],
                                },
                                {
                                    "source": [294.7063, 348.3968],
                                    "target": [10.668661594173, 48.726582481426],
                                },
                                {
                                    "source": [179.0402, 448.7842],
                                    "target": [10.643736719976, 48.711748022874],
                                },
                                {
                                    "source": [623.7357, 80.2668],
                                    "target": [10.739638209288, 48.765643779367],
                                },
                                {
                                    "source": [659.0273, 517.9686],
                                    "target": [10.748037099729, 48.70257582834],
                                },
                            ],
                        }
                    ),
                    clip=json.dumps(
                        {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.620311648, 48.764715154],
                                    [10.620304942, 48.76471869],
                                    [10.620310306, 48.76471648],
                                    [10.747275352, 48.765701238],
                                    [10.748301744, 48.681741906],
                                    [10.62171042, 48.680702374],
                                    [10.621619224, 48.680705916],
                                    [10.621563495, 48.68075816],
                                    [10.62159419, 48.680721855],
                                    [10.620309412, 48.764715596],
                                    [10.620311648, 48.764715154],
                                ]
                            ],
                        }
                    ),
                    target_crs=4326,
                    validation=EnumValidationValue.VALID.value,
                    raw_map_id=map_id,
                    overwrites=0,
                    comment=None,
                )
            )
            session.commit()

        # Build test request
        json_request = json.dumps(
            {
                "transformation_id": 8916,
            }
        )

        res = test_client.post(
            "/transformations?dry_run=true",
            data=json_request,
        )

        assert res.status_code == 200
        result = res.json()
        assert "extent" in result
        assert "layer_name" in result
        assert "wms_url" in result
        assert "job_id" not in result
        assert "transformation_id" not in result
        assert "points" not in result

    def test_post_transformation_success_dry_run_with_clip(
        self, test_client, override_get_session, override_get_user_from_session
    ):
        # Build test request
        json_request = json.dumps(
            {
                "params": {
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
                            "source": [719.4964, 124.8117],
                            "target": [14.809553411787, 50.894672081543],
                        },
                        {
                            "source": [719.4964, 124.8117],
                            "target": [14.809553411787, 50.894672081543],
                        },
                    ],
                },
                "clip": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [14.66364715, 50.899831877],
                            [14.661734495, 50.799776765],
                            [14.76482527, 50.800276974],
                            [14.76601098, 50.800290518],
                            [14.766134477, 50.790482954],
                            [14.782466161, 50.790564091],
                            [14.782294867, 50.800358074],
                            [14.829388684, 50.800594678],
                            [14.829132977, 50.900185772],
                            [14.829130294, 50.900185772],
                            [14.66364715, 50.899831877],
                        ]
                    ],
                },
                "map_id": to_public_map_id(10001556),
                "overwrites": 0,
                "user_id": "test",
            }
        )

        res = test_client.post(
            "/transformations?dry_run=true",
            data=json_request,
        )

        assert res.status_code == 200
        result = res.json()
        assert "extent" in result
        assert "layer_name" in result
        assert "wms_url" in result
        assert "job_id" not in result
        assert "transformation_id" not in result
        assert "points" not in result

    def test_post_transformations_success_new_transformation(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
        db_container,
    ):
        map_id = 10001558

        with Session(db_container[1]) as session:
            # Setup test data
            session.add(
                RawMap(
                    id=map_id,
                    file_name="df_dk_0010001_3352_191s8",
                    enabled=False,
                    map_type="M",
                    default_crs=4314,
                    rel_path="",
                    allow_download=False,
                    map_scale=1000,
                )
            )
            session.commit()

        # Create and perform test request
        json_request = {
            "clip": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [14.66364715, 50.899831877],
                        [14.661734495, 50.799776765],
                        [14.76482527, 50.800276974],
                        [14.76601098, 50.800290518],
                        [14.766134477, 50.790482954],
                        [14.782466161, 50.790564091],
                        [14.782294867, 50.800358074],
                        [14.829388684, 50.800594678],
                        [14.829132977, 50.900185772],
                        [14.829130294, 50.900185772],
                        [14.66364715, 50.899831877],
                    ]
                ],
            },
            "params": {
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
                    {
                        "source": [805.2507, 101.0329],
                        "target": [14.829138205432, 50.898323450806],
                    },
                    {
                        "source": [805.1431, 124.8117],
                        "target": [14.829145688426, 50.894908648825],
                    },
                    {
                        "source": [804.6051, 257.3703],
                        "target": [14.829196331602, 50.874764134307],
                    },
                    {
                        "source": [803.8519, 414.1382],
                        "target": [14.829253978805, 50.852910617897],
                    },
                    {
                        "source": [803.2064, 731.9776],
                        "target": [14.829363593315, 50.80734546335],
                    },
                    {
                        "source": [803.0988, 603.7228],
                        "target": [14.829323125954, 50.825911023952],
                    },
                    {
                        "source": [760.9210, 87.7986],
                        "target": [14.818461581754, 50.900162259197],
                    },
                    {
                        "source": [733.3764, 87.6910],
                        "target": [14.812297813421, 50.900151361887],
                    },
                    {
                        "source": [690.8758, 87.4758],
                        "target": [14.802223053593, 50.900129107788],
                    },
                    {
                        "source": [712.0723, 87.5834],
                        "target": [14.807439741575, 50.900140443422],
                    },
                    {
                        "source": [655.7994, 87.2606],
                        "target": [14.79396136798, 50.900113591633],
                    },
                    {
                        "source": [612.8685, 87.0454],
                        "target": [14.783920384473, 50.900090067859],
                    },
                    {
                        "source": [497.9557, 86.2922],
                        "target": [14.75775378559, 50.900032966778],
                    },
                    {
                        "source": [464.2780, 85.8618],
                        "target": [14.750505879687, 50.900016164954],
                    },
                    {
                        "source": [472.5629, 86.1846],
                        "target": [14.752365899551, 50.900022902391],
                    },
                    {
                        "source": [230.6865, 84.6783],
                        "target": [14.696740414531, 50.899902828324],
                    },
                    {
                        "source": [293.7379, 84.8935],
                        "target": [14.711380112251, 50.899935584721],
                    },
                    {
                        "source": [156.4450, 96.1911],
                        "target": [14.678838241912, 50.898270458088],
                    },
                    {
                        "source": [227.0282, 84.6783],
                        "target": [14.695619330344, 50.899901154426],
                    },
                    {
                        "source": [186.0340, 84.5707],
                        "target": [14.685688820994, 50.899880165294],
                    },
                    {
                        "source": [84.7859, 133.4194],
                        "target": [14.663512309453, 50.892726856692],
                    },
                    {
                        "source": [84.7859, 97.9126],
                        "target": [14.663606153878, 50.897668380513],
                    },
                    {
                        "source": [84.5707, 291.8012],
                        "target": [14.663059846595, 50.869356442866],
                    },
                    {
                        "source": [84.1403, 417.2584],
                        "target": [14.662716360693, 50.851226910756],
                    },
                    {
                        "source": [83.4947, 530.9877],
                        "target": [14.662403924156, 50.835015826507],
                    },
                    {
                        "source": [83.3871, 672.3693],
                        "target": [14.66201809743, 50.814587799125],
                    },
                    {
                        "source": [121.4762, 775.5541],
                        "target": [14.671402656065, 50.799822388914],
                    },
                    {
                        "source": [306.3267, 776.4149],
                        "target": [14.71494617521, 50.80003532242],
                    },
                    {
                        "source": [541.1018, 777.0605],
                        "target": [14.769027444289, 50.800301490166],
                    },
                    {
                        "source": [740.0473, 777.7060],
                        "target": [14.814811178089, 50.800522857232],
                    },
                    {
                        "source": [252.2057, 573.3807],
                        "target": [14.702654426308, 50.828966502252],
                    },
                    {
                        "source": [347.2133, 613.6217],
                        "target": [14.724240369322, 50.823275953506],
                    },
                    {
                        "source": [365.9350, 613.5141],
                        "target": [14.728240875224, 50.823645316122],
                    },
                    {
                        "source": [383.4732, 690.6606],
                        "target": [14.732725721035, 50.812001813382],
                    },
                    {
                        "source": [543.8993, 708.1988],
                        "target": [14.769530816595, 50.809901028317],
                    },
                    {
                        "source": [542.2853, 714.5470],
                        "target": [14.769256299665, 50.808950066353],
                    },
                    {
                        "source": [708.7368, 612.1153],
                        "target": [14.807585452192, 50.824413387287],
                    },
                    {
                        "source": [586.8302, 656.4450],
                        "target": [14.779585654499, 50.817950250277],
                    },
                    {
                        "source": [463.4173, 715.1926],
                        "target": [14.751634272656, 50.808613014558],
                    },
                    {
                        "source": [599.7418, 777.1681],
                        "target": [14.782296084065, 50.800354683619],
                    },
                    {
                        "source": [145.6854, 84.3555],
                        "target": [14.67634612815, 50.899859802211],
                    },
                    {
                        "source": [257.0476, 84.6783],
                        "target": [14.701935480532, 50.899914589163],
                    },
                    {
                        "source": [411.4482, 178.8250],
                        "target": [14.738689286797, 50.886536375438],
                    },
                    {
                        "source": [346.8905, 213.9014],
                        "target": [14.724086779327, 50.881400957462],
                    },
                    {
                        "source": [598.3430, 200.7747],
                        "target": [14.781628702951, 50.883739028779],
                    },
                    {
                        "source": [536.1524, 284.3770],
                        "target": [14.767642016105, 50.871542857],
                    },
                    {
                        "source": [508.5001, 322.0357],
                        "target": [14.761426208635, 50.866146613586],
                    },
                    {
                        "source": [188.5087, 265.3325],
                        "target": [14.686777727172, 50.873739758153],
                    },
                    {
                        "source": [228.1042, 352.2703],
                        "target": [14.695887327077, 50.860745617059],
                    },
                    {
                        "source": [662.0400, 360.9856],
                        "target": [14.796487598134, 50.860512023302],
                    },
                    {
                        "source": [277.7060, 709.2748],
                        "target": [14.708445231744, 50.809621467831],
                    },
                    {
                        "source": [323.7573, 429.5244],
                        "target": [14.718511063861, 50.849750438399],
                    },
                    {
                        "source": [773.4022, 777.8136],
                        "target": [14.822605684397, 50.800558336973],
                    },
                    {
                        "source": [442.3284, 407.2520],
                        "target": [14.745949775376, 50.85370368877],
                    },
                    {
                        "source": [431.0308, 388.9606],
                        "target": [14.743331660827, 50.856337080476],
                    },
                    {
                        "source": [418.8724, 373.5743],
                        "target": [14.740705479905, 50.858508042521],
                    },
                    {
                        "source": [402.0874, 493.7594],
                        "target": [14.737042129051, 50.840928706352],
                    },
                    {
                        "source": [612.7609, 504.3039],
                        "target": [14.785700030341, 50.840037938729],
                    },
                    {
                        "source": [362.2767, 85.3239],
                        "target": [14.727518573288, 50.899969586806],
                    },
                    {
                        "source": [84.8935, 151.7108],
                        "target": [14.663452240739, 50.889766853181],
                    },
                    {
                        "source": [84.2479, 389.3910],
                        "target": [14.662793178389, 50.855212017021],
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
            "overwrites": 0,
            "map_id": to_public_map_id(map_id),
        }

        # Build test request
        res = test_client.post(
            "/transformations",
            data=json.dumps(json_request),
        )

        # Run tests
        assert res.status_code == 200
        result = res.json()
        assert result["transformation_id"] is not None
        assert result["job_id"] is not None
        assert result["points"] == 400

    def test_post_transformations_success_new_transformation_multiple_times(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
        db_container,
    ):
        map_id = 10001558

        with Session(db_container[1]) as session:
            # Setup test data
            session.add(
                RawMap(
                    id=map_id,
                    file_name="df_dk_0010001_3352_191s8",
                    enabled=False,
                    map_type="M",
                    default_crs=4314,
                    rel_path="",
                    allow_download=False,
                )
            )
            session.commit()

        # Create and perform test request
        params = {
            "clip": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [14.66364715, 50.899831877],
                        [14.661734495, 50.799776765],
                        [14.76482527, 50.800276974],
                        [14.76601098, 50.800290518],
                        [14.766134477, 50.790482954],
                        [14.782466161, 50.790564091],
                        [14.782294867, 50.800358074],
                        [14.829388684, 50.800594678],
                        [14.829132977, 50.900185772],
                        [14.829130294, 50.900185772],
                        [14.66364715, 50.899831877],
                    ]
                ],
            },
            "params": {
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
                    {
                        "source": [805.2507, 101.0329],
                        "target": [14.829138205432, 50.898323450806],
                    },
                    {
                        "source": [805.1431, 124.8117],
                        "target": [14.829145688426, 50.894908648825],
                    },
                    {
                        "source": [804.6051, 257.3703],
                        "target": [14.829196331602, 50.874764134307],
                    },
                    {
                        "source": [803.8519, 414.1382],
                        "target": [14.829253978805, 50.852910617897],
                    },
                    {
                        "source": [803.2064, 731.9776],
                        "target": [14.829363593315, 50.80734546335],
                    },
                    {
                        "source": [803.0988, 603.7228],
                        "target": [14.829323125954, 50.825911023952],
                    },
                    {
                        "source": [760.9210, 87.7986],
                        "target": [14.818461581754, 50.900162259197],
                    },
                    {
                        "source": [733.3764, 87.6910],
                        "target": [14.812297813421, 50.900151361887],
                    },
                    {
                        "source": [690.8758, 87.4758],
                        "target": [14.802223053593, 50.900129107788],
                    },
                    {
                        "source": [712.0723, 87.5834],
                        "target": [14.807439741575, 50.900140443422],
                    },
                    {
                        "source": [655.7994, 87.2606],
                        "target": [14.79396136798, 50.900113591633],
                    },
                    {
                        "source": [612.8685, 87.0454],
                        "target": [14.783920384473, 50.900090067859],
                    },
                    {
                        "source": [497.9557, 86.2922],
                        "target": [14.75775378559, 50.900032966778],
                    },
                    {
                        "source": [464.2780, 85.8618],
                        "target": [14.750505879687, 50.900016164954],
                    },
                    {
                        "source": [472.5629, 86.1846],
                        "target": [14.752365899551, 50.900022902391],
                    },
                    {
                        "source": [230.6865, 84.6783],
                        "target": [14.696740414531, 50.899902828324],
                    },
                    {
                        "source": [293.7379, 84.8935],
                        "target": [14.711380112251, 50.899935584721],
                    },
                    {
                        "source": [156.4450, 96.1911],
                        "target": [14.678838241912, 50.898270458088],
                    },
                    {
                        "source": [227.0282, 84.6783],
                        "target": [14.695619330344, 50.899901154426],
                    },
                    {
                        "source": [186.0340, 84.5707],
                        "target": [14.685688820994, 50.899880165294],
                    },
                    {
                        "source": [84.7859, 133.4194],
                        "target": [14.663512309453, 50.892726856692],
                    },
                    {
                        "source": [84.7859, 97.9126],
                        "target": [14.663606153878, 50.897668380513],
                    },
                    {
                        "source": [84.5707, 291.8012],
                        "target": [14.663059846595, 50.869356442866],
                    },
                    {
                        "source": [84.1403, 417.2584],
                        "target": [14.662716360693, 50.851226910756],
                    },
                    {
                        "source": [83.4947, 530.9877],
                        "target": [14.662403924156, 50.835015826507],
                    },
                    {
                        "source": [83.3871, 672.3693],
                        "target": [14.66201809743, 50.814587799125],
                    },
                    {
                        "source": [121.4762, 775.5541],
                        "target": [14.671402656065, 50.799822388914],
                    },
                    {
                        "source": [306.3267, 776.4149],
                        "target": [14.71494617521, 50.80003532242],
                    },
                    {
                        "source": [541.1018, 777.0605],
                        "target": [14.769027444289, 50.800301490166],
                    },
                    {
                        "source": [740.0473, 777.7060],
                        "target": [14.814811178089, 50.800522857232],
                    },
                    {
                        "source": [252.2057, 573.3807],
                        "target": [14.702654426308, 50.828966502252],
                    },
                    {
                        "source": [347.2133, 613.6217],
                        "target": [14.724240369322, 50.823275953506],
                    },
                    {
                        "source": [365.9350, 613.5141],
                        "target": [14.728240875224, 50.823645316122],
                    },
                    {
                        "source": [383.4732, 690.6606],
                        "target": [14.732725721035, 50.812001813382],
                    },
                    {
                        "source": [543.8993, 708.1988],
                        "target": [14.769530816595, 50.809901028317],
                    },
                    {
                        "source": [542.2853, 714.5470],
                        "target": [14.769256299665, 50.808950066353],
                    },
                    {
                        "source": [708.7368, 612.1153],
                        "target": [14.807585452192, 50.824413387287],
                    },
                    {
                        "source": [586.8302, 656.4450],
                        "target": [14.779585654499, 50.817950250277],
                    },
                    {
                        "source": [463.4173, 715.1926],
                        "target": [14.751634272656, 50.808613014558],
                    },
                    {
                        "source": [599.7418, 777.1681],
                        "target": [14.782296084065, 50.800354683619],
                    },
                    {
                        "source": [145.6854, 84.3555],
                        "target": [14.67634612815, 50.899859802211],
                    },
                    {
                        "source": [257.0476, 84.6783],
                        "target": [14.701935480532, 50.899914589163],
                    },
                    {
                        "source": [411.4482, 178.8250],
                        "target": [14.738689286797, 50.886536375438],
                    },
                    {
                        "source": [346.8905, 213.9014],
                        "target": [14.724086779327, 50.881400957462],
                    },
                    {
                        "source": [598.3430, 200.7747],
                        "target": [14.781628702951, 50.883739028779],
                    },
                    {
                        "source": [536.1524, 284.3770],
                        "target": [14.767642016105, 50.871542857],
                    },
                    {
                        "source": [508.5001, 322.0357],
                        "target": [14.761426208635, 50.866146613586],
                    },
                    {
                        "source": [188.5087, 265.3325],
                        "target": [14.686777727172, 50.873739758153],
                    },
                    {
                        "source": [228.1042, 352.2703],
                        "target": [14.695887327077, 50.860745617059],
                    },
                    {
                        "source": [662.0400, 360.9856],
                        "target": [14.796487598134, 50.860512023302],
                    },
                    {
                        "source": [277.7060, 709.2748],
                        "target": [14.708445231744, 50.809621467831],
                    },
                    {
                        "source": [323.7573, 429.5244],
                        "target": [14.718511063861, 50.849750438399],
                    },
                    {
                        "source": [773.4022, 777.8136],
                        "target": [14.822605684397, 50.800558336973],
                    },
                    {
                        "source": [442.3284, 407.2520],
                        "target": [14.745949775376, 50.85370368877],
                    },
                    {
                        "source": [431.0308, 388.9606],
                        "target": [14.743331660827, 50.856337080476],
                    },
                    {
                        "source": [418.8724, 373.5743],
                        "target": [14.740705479905, 50.858508042521],
                    },
                    {
                        "source": [402.0874, 493.7594],
                        "target": [14.737042129051, 50.840928706352],
                    },
                    {
                        "source": [612.7609, 504.3039],
                        "target": [14.785700030341, 50.840037938729],
                    },
                    {
                        "source": [362.2767, 85.3239],
                        "target": [14.727518573288, 50.899969586806],
                    },
                    {
                        "source": [84.8935, 151.7108],
                        "target": [14.663452240739, 50.889766853181],
                    },
                    {
                        "source": [84.2479, 389.3910],
                        "target": [14.662793178389, 50.855212017021],
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
            "overwrites": 0,
            "map_id": to_public_map_id(map_id),
        }

        # Build test request
        res = test_client.post(
            "/transformations",
            data=json.dumps(params),
        )

        # Run tests
        assert res.status_code == 200
        result = res.json()
        assert result["transformation_id"] is not None
        assert result["job_id"] is not None
        assert result["points"] == 400

        res = test_client.post(
            "/transformations",
            data=json.dumps(params),
        )
        assert res.status_code == 400

        res = test_client.post(
            "/transformations",
            data=json.dumps(params),
        )

        assert res.status_code == 400

    def test_post_transformations_success_new_transformation_without_clip(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
        db_container,
    ):
        map_id = 10001558

        with Session(db_container[1]) as session:
            # Setup test data
            session.add(
                RawMap(
                    id=map_id,
                    file_name="df_dk_0010001_3352_191s8",
                    enabled=False,
                    map_type="M",
                    default_crs=4314,
                    rel_path="",
                    allow_download=False,
                    map_scale=1,
                )
            )

            session.commit()

        # Create and perform test request
        params = {
            "params": {
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
                    {
                        "source": [805.2507, 101.0329],
                        "target": [14.829138205432, 50.898323450806],
                    },
                    {
                        "source": [805.1431, 124.8117],
                        "target": [14.829145688426, 50.894908648825],
                    },
                    {
                        "source": [804.6051, 257.3703],
                        "target": [14.829196331602, 50.874764134307],
                    },
                    {
                        "source": [803.8519, 414.1382],
                        "target": [14.829253978805, 50.852910617897],
                    },
                    {
                        "source": [803.2064, 731.9776],
                        "target": [14.829363593315, 50.80734546335],
                    },
                    {
                        "source": [803.0988, 603.7228],
                        "target": [14.829323125954, 50.825911023952],
                    },
                    {
                        "source": [760.9210, 87.7986],
                        "target": [14.818461581754, 50.900162259197],
                    },
                    {
                        "source": [733.3764, 87.6910],
                        "target": [14.812297813421, 50.900151361887],
                    },
                    {
                        "source": [690.8758, 87.4758],
                        "target": [14.802223053593, 50.900129107788],
                    },
                    {
                        "source": [712.0723, 87.5834],
                        "target": [14.807439741575, 50.900140443422],
                    },
                    {
                        "source": [655.7994, 87.2606],
                        "target": [14.79396136798, 50.900113591633],
                    },
                    {
                        "source": [612.8685, 87.0454],
                        "target": [14.783920384473, 50.900090067859],
                    },
                    {
                        "source": [497.9557, 86.2922],
                        "target": [14.75775378559, 50.900032966778],
                    },
                    {
                        "source": [464.2780, 85.8618],
                        "target": [14.750505879687, 50.900016164954],
                    },
                    {
                        "source": [472.5629, 86.1846],
                        "target": [14.752365899551, 50.900022902391],
                    },
                    {
                        "source": [230.6865, 84.6783],
                        "target": [14.696740414531, 50.899902828324],
                    },
                    {
                        "source": [293.7379, 84.8935],
                        "target": [14.711380112251, 50.899935584721],
                    },
                    {
                        "source": [156.4450, 96.1911],
                        "target": [14.678838241912, 50.898270458088],
                    },
                    {
                        "source": [227.0282, 84.6783],
                        "target": [14.695619330344, 50.899901154426],
                    },
                    {
                        "source": [186.0340, 84.5707],
                        "target": [14.685688820994, 50.899880165294],
                    },
                    {
                        "source": [84.7859, 133.4194],
                        "target": [14.663512309453, 50.892726856692],
                    },
                    {
                        "source": [84.7859, 97.9126],
                        "target": [14.663606153878, 50.897668380513],
                    },
                    {
                        "source": [84.5707, 291.8012],
                        "target": [14.663059846595, 50.869356442866],
                    },
                    {
                        "source": [84.1403, 417.2584],
                        "target": [14.662716360693, 50.851226910756],
                    },
                    {
                        "source": [83.4947, 530.9877],
                        "target": [14.662403924156, 50.835015826507],
                    },
                    {
                        "source": [83.3871, 672.3693],
                        "target": [14.66201809743, 50.814587799125],
                    },
                    {
                        "source": [121.4762, 775.5541],
                        "target": [14.671402656065, 50.799822388914],
                    },
                    {
                        "source": [306.3267, 776.4149],
                        "target": [14.71494617521, 50.80003532242],
                    },
                    {
                        "source": [541.1018, 777.0605],
                        "target": [14.769027444289, 50.800301490166],
                    },
                    {
                        "source": [740.0473, 777.7060],
                        "target": [14.814811178089, 50.800522857232],
                    },
                    {
                        "source": [252.2057, 573.3807],
                        "target": [14.702654426308, 50.828966502252],
                    },
                    {
                        "source": [347.2133, 613.6217],
                        "target": [14.724240369322, 50.823275953506],
                    },
                    {
                        "source": [365.9350, 613.5141],
                        "target": [14.728240875224, 50.823645316122],
                    },
                    {
                        "source": [383.4732, 690.6606],
                        "target": [14.732725721035, 50.812001813382],
                    },
                    {
                        "source": [543.8993, 708.1988],
                        "target": [14.769530816595, 50.809901028317],
                    },
                    {
                        "source": [542.2853, 714.5470],
                        "target": [14.769256299665, 50.808950066353],
                    },
                    {
                        "source": [708.7368, 612.1153],
                        "target": [14.807585452192, 50.824413387287],
                    },
                    {
                        "source": [586.8302, 656.4450],
                        "target": [14.779585654499, 50.817950250277],
                    },
                    {
                        "source": [463.4173, 715.1926],
                        "target": [14.751634272656, 50.808613014558],
                    },
                    {
                        "source": [599.7418, 777.1681],
                        "target": [14.782296084065, 50.800354683619],
                    },
                    {
                        "source": [145.6854, 84.3555],
                        "target": [14.67634612815, 50.899859802211],
                    },
                    {
                        "source": [257.0476, 84.6783],
                        "target": [14.701935480532, 50.899914589163],
                    },
                    {
                        "source": [411.4482, 178.8250],
                        "target": [14.738689286797, 50.886536375438],
                    },
                    {
                        "source": [346.8905, 213.9014],
                        "target": [14.724086779327, 50.881400957462],
                    },
                    {
                        "source": [598.3430, 200.7747],
                        "target": [14.781628702951, 50.883739028779],
                    },
                    {
                        "source": [536.1524, 284.3770],
                        "target": [14.767642016105, 50.871542857],
                    },
                    {
                        "source": [508.5001, 322.0357],
                        "target": [14.761426208635, 50.866146613586],
                    },
                    {
                        "source": [188.5087, 265.3325],
                        "target": [14.686777727172, 50.873739758153],
                    },
                    {
                        "source": [228.1042, 352.2703],
                        "target": [14.695887327077, 50.860745617059],
                    },
                    {
                        "source": [662.0400, 360.9856],
                        "target": [14.796487598134, 50.860512023302],
                    },
                    {
                        "source": [277.7060, 709.2748],
                        "target": [14.708445231744, 50.809621467831],
                    },
                    {
                        "source": [323.7573, 429.5244],
                        "target": [14.718511063861, 50.849750438399],
                    },
                    {
                        "source": [773.4022, 777.8136],
                        "target": [14.822605684397, 50.800558336973],
                    },
                    {
                        "source": [442.3284, 407.2520],
                        "target": [14.745949775376, 50.85370368877],
                    },
                    {
                        "source": [431.0308, 388.9606],
                        "target": [14.743331660827, 50.856337080476],
                    },
                    {
                        "source": [418.8724, 373.5743],
                        "target": [14.740705479905, 50.858508042521],
                    },
                    {
                        "source": [402.0874, 493.7594],
                        "target": [14.737042129051, 50.840928706352],
                    },
                    {
                        "source": [612.7609, 504.3039],
                        "target": [14.785700030341, 50.840037938729],
                    },
                    {
                        "source": [362.2767, 85.3239],
                        "target": [14.727518573288, 50.899969586806],
                    },
                    {
                        "source": [84.8935, 151.7108],
                        "target": [14.663452240739, 50.889766853181],
                    },
                    {
                        "source": [84.2479, 389.3910],
                        "target": [14.662793178389, 50.855212017021],
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
            "overwrites": 0,
            "map_id": to_public_map_id(map_id),
        }

        # Build test request
        res = test_client.post(
            "/transformations",
            data=json.dumps(params),
        )

        # Run tests
        assert res.status_code == 200
        result = res.json()
        assert result["transformation_id"] is not None
        assert result["job_id"] is not None
        assert result["points"] == 400

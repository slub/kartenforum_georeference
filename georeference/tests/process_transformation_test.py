#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from datetime import datetime

from sqlmodel import Session, select

from georeference.config.settings import get_settings
from georeference.jobs.process_transformation import run_process_new_transformation
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.georef_map import GeorefMap
from georeference.models.job import Job
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation, EnumValidationValue
from georeference.utils.parser import to_public_map_id


def test_run_process_jobs_success(db_container, es_index):
    """The test checks the proper running of the process jobs"""
    # Create the test data

    with Session(db_container[1]) as session:
        map_id = 10010367
        new_job = Job(
            id=10000000,
            submitted=datetime.now(),
            user_id="test",
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 10000001 }',
            state=EnumJobState.NOT_STARTED.value,
        )
        session.add(
            Transformation(
                id=10000001,
                submitted=datetime.now(),
                user_id="test",
                params=json.dumps(
                    {
                        "source": "pixel",
                        "target": "EPSG:4314",
                        "algorithm": "affine",
                        "gcps": [
                            {
                                "source": [55.4411, 90.2791],
                                "target": [16.499998092651, 51.900001525879],
                            },
                            {
                                "source": [55.0665, 698.5391],
                                "target": [16.499998092651, 51.79999923706],
                            },
                            {
                                "source": [682.8058, 698.5391],
                                "target": [16.666667938232, 51.79999923706],
                            },
                            {
                                "source": [682.6185, 91.0283],
                                "target": [16.666667938232, 51.900001525879],
                            },
                        ],
                    }
                ),
                target_crs=4314,
                validation=EnumValidationValue.MISSING.value,
                raw_map_id=map_id,
                overwrites=0,
                comment=None,
                clip=json.dumps(
                    {
                        "crs": {"type": "name", "properties": {"name": "EPSG:4314"}},
                        "coordinates": [
                            [
                                [16.5000353928, 51.900032347],
                                [16.4999608259, 51.7999684435],
                                [16.666705251, 51.8000300686],
                                [16.6666305921, 51.8999706667],
                                [16.5000353928, 51.900032347],
                            ]
                        ],
                        "type": "Polygon",
                    }
                ),
            )
        )
        session.commit()
        session.add(new_job)
        session.commit()

        # Normally the tms processing needs really long. To prevent this we temporary increase the map_scale of the RawMap
        # to trigger lower zoom levels
        raw_map_obj = RawMap.by_id(map_id, session)
        raw_map_obj.map_scale = 1000000000
        session.commit()

        # Build test request
        run_process_new_transformation(es_index, session, new_job)

        # Check if the database changes are correct
        g = session.exec(
            select(GeorefMap).where(GeorefMap.transformation_id == 10000001)
        ).first()

        assert g is not None

        settings = get_settings()
        # Check if the index was pushed to the es
        assert (
            es_index.get(settings.ES_INDEX_NAME, id=to_public_map_id(map_id))
            is not None
        )

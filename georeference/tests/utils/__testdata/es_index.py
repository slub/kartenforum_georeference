#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 15.05.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

from datetime import datetime, date
from uuid import uuid4

from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.models.mosaic_map import MosaicMap
from georeference.models.vector_map import VectorMap
from georeference.models.vector_map_external import VectorMapExternal


def mock_factory(start_date: datetime, end_date: datetime):
    mock_vector_map = VectorMap(
        title="bla",
        description="bla",
        link_thumb="https://bla.bla",
        time_period=[start_date, end_date],
        submitted=datetime.now(),
        last_change=datetime.now(),
        public_id=uuid4(),
    )

    mock_external_vector_map = VectorMapExternal(
        title="bla",
        description="bla",
        link_thumb="https://bla.bla",
        link_content="https://bla.bla",
        time_period=[start_date, end_date],
        submitted=datetime.now(),
        last_change=datetime.now(),
        public_id=uuid4(),
    )

    mock_raw_map = RawMap(
        id=1,
        allow_download=False,
        file_name="bla",
        enabled=True,
        map_type="bla",
        default_crs=0,
        rel_path="bla",
        map_scale=2000,
    )

    mock_metadata_raw_map = Metadata(
        title="bla", title_short="bla", time_of_publication=start_date
    )

    mock_mosaic_map = MosaicMap(
        id=1,
        raw_map_ids=[1, 2, 3],
        title="mosaicbla",
        time_of_publication=start_date,
        name="bla",
        title_short="bla",
        description="bla",
        link_thumb="https:bla.bls",
        map_scale=2000,
    )

    return {
        "metadata_raw_map": mock_metadata_raw_map,
        "mosaic_map": mock_mosaic_map,
        "vector_map": mock_vector_map,
        "external_vector_map": mock_external_vector_map,
        "raw_map": mock_raw_map,
    }


def get_time_range_query(start: date, end: date):
    # periods are intersecting when (start_a <= end_b) AND (end_a >= start_b)
    return {
        "bool": {
            "filter": [
                {
                    "range": {"time_period_start": {"lte": end.isoformat()}},
                },
                {
                    "range": {"time_period_end": {"gte": start.isoformat()}},
                },
            ]
        }
    }


# map period is expected to be [2025-01-01, 2025-12-31]
time_period_queries = [
    # end dates are touching
    (get_time_range_query(date(2000, 1, 1), date(2025, 12, 31)), True),
    # start dates are touching
    (get_time_range_query(date(2025, 1, 1), date(2100, 1, 1)), True),
    # search period encloses map period
    (get_time_range_query(date(2000, 1, 1), date(2100, 1, 1)), True),
    # search period is inside map period
    (get_time_range_query(date(2025, 5, 1), date(2025, 5, 25)), True),
    # search period is inside map period on a single day
    (get_time_range_query(date(2025, 5, 1), date(2025, 5, 1)), True),
    # search period end is within map period
    (get_time_range_query(date(2000, 1, 1), date(2025, 5, 1)), True),
    # search period start is within map period
    (get_time_range_query(date(2025, 5, 1), date(2100, 1, 1)), True),
    # invalid
    (get_time_range_query(date(2001, 1, 1), date(2001, 2, 1)), False),
    (get_time_range_query(date(2100, 1, 1), date(2100, 2, 1)), False),
]

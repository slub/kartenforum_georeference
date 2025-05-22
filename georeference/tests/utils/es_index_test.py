#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 15.05.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

import pytest

from datetime import datetime
from testcontainers.core.waiting_utils import time
from georeference.config.settings import get_settings

from georeference.utils.es_index.document_formatter import (
    generate_es_vector_map_document,
    generate_es_original_map_document,
    generate_es_mosaic_map_document,
)

from georeference.tests.utils.__testdata.es_index import (
    mock_factory,
    time_period_queries,
)


class TestEsSearchIndex:
    @pytest.mark.parametrize("valid_query,is_expected", time_period_queries)
    def test_time_period_query_success(self, valid_query, is_expected, es_index):
        settings = get_settings()
        index_name = settings.ES_INDEX_NAME

        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)
        mocks = mock_factory(start_date=start_date, end_date=end_date)

        mock_raw_map = mocks["raw_map"]
        mock_mosaic_map = mocks["mosaic_map"]
        mock_external_vector_map = mocks["external_vector_map"]
        mock_vector_map = mocks["vector_map"]
        mock_metadata_raw_map = mocks["metadata_raw_map"]

        es_doc_mosaic = generate_es_mosaic_map_document(mosaic_map_obj=mock_mosaic_map)

        es_index.index(
            index=index_name,
            doc_type=None,
            id=es_doc_mosaic["map_id"],
            document=es_doc_mosaic,
        )

        es_index.index(
            index=index_name,
            doc_type=None,
            id=mock_raw_map.id,
            document=generate_es_original_map_document(
                raw_map_obj=mock_raw_map, metadata_obj=mock_metadata_raw_map
            ),
        )

        es_index.index(
            index=index_name,
            doc_type=None,
            id=mock_vector_map.public_id,
            document=generate_es_vector_map_document(mock_vector_map),
        )

        es_index.index(
            index=index_name,
            doc_type=None,
            id=mock_external_vector_map.public_id,
            document=generate_es_vector_map_document(mock_external_vector_map),
        )

        # not ideal, otherwise results are empty
        # awaiting doc creation w/ pytest-asyncio didn't do the trick either
        time.sleep(1)

        result = es_index.search(index=index_name, query=valid_query)
        test = result["hits"]["total"]["value"] == 4
        assert test == is_expected

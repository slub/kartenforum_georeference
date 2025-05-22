#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 14.05.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

import pytest
from datetime import datetime
from sqlmodel import Session

from georeference.config.settings import get_settings

from georeference.models.vector_map import VectorMap, VectorMapRoles, RoleEnum

from georeference.utils.es_index.document_formatter import (
    generate_es_vector_map_document,
)


# probably better to run a post request w/ the test client to populate the es index and db
# however i could not get the async es client to work w/ two requests in one test case
# see https://github.com/elastic/elasticsearch-py/issues/2051
# or: https://github.com/pytest-dev/pytest-asyncio/issues/991
@pytest.fixture(scope="function")
def provision_mock_vector_map(db_container, override_get_async_es_index):
    settings = get_settings()
    index_name = settings.ES_INDEX_NAME
    engine = db_container[1]

    with Session(engine) as session, override_get_async_es_index as es_sync:
        mock = VectorMap(
            title="bla",
            description="bla",
            link_thumb="https://bla.bla",
            time_period=["2025-01-01", "2026-01-01"],
            submitted=datetime.now(),
            last_change=datetime.now(),
        )

        session.add(mock)
        session.commit()
        session.refresh(mock)

        mock_role = VectorMapRoles(
            vector_map_id=mock.id,
            user_id="test_user",
            role=RoleEnum.owner,
        )

        session.add(mock_role)
        session.commit()
        session.refresh(mock_role)

        es_sync.index(
            index=index_name,
            doc_type=None,
            id=mock.public_id,
            document=generate_es_vector_map_document(mock),
        )

    # add clean up
    # works for now, as test containers are always run in function scope

    return mock

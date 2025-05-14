#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 02.05.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

import pytest
from datetime import datetime
from sqlmodel import Session

from georeference.config.settings import get_settings
from georeference.main import app
from georeference.models.vector_map_external import VectorMapExternal
from georeference.tests.routers.__test_data.vector_maps_external import (
    empty_geojson,
    invalid_geojson,
)
from georeference.utils.es_index.document_formatter import (
    generate_es_vector_map_document,
)
from georeference.utils.http_client import get_http_client


class MockResponse:
    def raise_for_status(*args, **kwargs):
        pass

    def json(*args, **kwargs):
        return empty_geojson


class MockResponseInvalid:
    def raise_for_status(*args, **kwargs):
        pass

    def json(*args, **kwargs):
        return invalid_geojson


class MockHttpClient:
    async def get(*args, **kwargs):
        return MockResponse()


class MockHttpClientInvalid:
    async def get(*args, **kwargs):
        return MockResponseInvalid()


@pytest.fixture(scope="function")
def override_get_http_client_with_invalid_response():
    app.dependency_overrides[get_http_client] = MockHttpClientInvalid

    yield

    del app.dependency_overrides[get_http_client]


@pytest.fixture(scope="function")
def override_get_http_client_with_valid_response():
    app.dependency_overrides[get_http_client] = MockHttpClient

    yield

    del app.dependency_overrides[get_http_client]


# probably better to run a post request w/ the test client to populate the es index and db
# however i could not get the async es client to work w/ two requests in one test case
# see https://github.com/elastic/elasticsearch-py/issues/2051
# or: https://github.com/pytest-dev/pytest-asyncio/issues/991
@pytest.fixture(scope="function")
def provision_mock_vector_map_external(db_container, override_get_async_es_index):
    settings = get_settings()
    index_name = settings.ES_INDEX_NAME
    engine = db_container[1]

    mock = VectorMapExternal(
        title="bla",
        description="bla",
        link_thumb="https://bla.bla",
        link_content="https://bla.bla",
        time_period=["2025-01-01", "2026-01-01"],
        submitted=datetime.now(),
        last_change=datetime.now(),
    )

    with Session(engine) as session:
        session.add(mock)
        session.commit()
        session.refresh(mock)

    with override_get_async_es_index as es_sync:
        es_sync.index(
            index=index_name,
            doc_type=None,
            id=mock.public_id,
            document=generate_es_vector_map_document(mock),
        )

    # add clean up
    # works for now, as test containers are always run in function scope

    return mock

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from pathlib import Path
from typing import Callable

import pytest
from sqlalchemy import Engine, create_engine
from sqlmodel import Session
from starlette.testclient import TestClient
from testcontainers.elasticsearch import ElasticSearchContainer
from testcontainers.postgres import PostgresContainer

from georeference import PYTHON_ROOT_DIR
from georeference.config.db import get_session
from georeference.config.settings import get_settings
from georeference.main import app
from georeference.schemas.user import User
from georeference.utils.auth import get_user_from_session
from georeference.utils.es_index import get_es_index


@pytest.fixture(scope="function")
def db_container(request) -> (PostgresContainer, Callable[[], Engine]):
    """
    Setup postgres container

    It will be recreated for each test function and thus can be modified without affecting other tests.
    """
    settings = get_settings()

    postgres_container = PostgresContainer(
        image="postgis/postgis:13-master",
        username=settings.POSTGRES_USER,
        port=settings.POSTGRES_PORT,
        password=settings.POSTGRES_PASSWORD,
    )

    # Setup initialization script
    init_script = Path(PYTHON_ROOT_DIR).parent / "docker" / "entrypoints" / "init-db.sh"
    path_as_string = str(init_script.absolute())

    postgres_container.with_volume_mapping(
        host=path_as_string, container=f"/docker-entrypoint-initdb.d/{init_script.name}"
    )

    # Start container and update host in settings

    postgres_container.start()
    postgres_container.dbname = "vkdb"

    db_engine = create_engine(
        postgres_container.get_connection_url(),
        pool_size=5,
        max_overflow=10,
    )

    # Store old dependency override if available
    def remove_container():
        postgres_container.stop()

    request.addfinalizer(remove_container)

    return (postgres_container, db_engine)


@pytest.fixture(scope="session")
def readonly_db_container(request) -> (PostgresContainer, Callable[[], Engine]):
    """
    Setup readonly postgres container

    => This fixture is used for tests that require a readonly database connection
    It does not need to be recreated for each test, so it is scoped to the session.
    """
    settings = get_settings()

    postgres_container = PostgresContainer(
        image="postgis/postgis:13-master",
        username=settings.POSTGRES_USER,
        port=settings.POSTGRES_PORT,
        password=settings.POSTGRES_PASSWORD,
    )

    # Setup initialization script
    init_script = Path(PYTHON_ROOT_DIR).parent / "docker" / "entrypoints" / "init-db.sh"
    path_as_string = str(init_script.absolute())

    postgres_container.with_volume_mapping(
        host=path_as_string, container=f"/docker-entrypoint-initdb.d/{init_script.name}"
    )

    # Start container and update host in settings
    container_ip = postgres_container.get_container_host_ip()

    postgres_container.start()
    postgres_container.dbname = "vkdb"

    # Set default transactions to read only
    postgres_container.exec(
        f"psql -U {settings.POSTGRES_USER} -d {container_ip} -c 'ALTER SYSTEM SET default_transaction_read_only TO on;' -c 'SELECT pg_reload_conf();'"
    )

    db_engine = create_engine(
        postgres_container.get_connection_url(),
        pool_size=5,
        max_overflow=10,
    )

    def remove_container():
        postgres_container.stop()

    request.addfinalizer(remove_container)

    return (postgres_container, db_engine)


@pytest.fixture(scope="function")
def override_get_session_read_only(readonly_db_container):
    def override_get_session():
        with Session(readonly_db_container[1]) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    yield

    del app.dependency_overrides[get_session]


@pytest.fixture(scope="function")
def override_get_session(db_container):
    def override_get_session():
        with Session(db_container[1]) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    yield

    del app.dependency_overrides[get_session]


# Allows overriding of the authentication functions in tests with a static user
@pytest.fixture()
def override_get_user_from_session(request):
    def override_check_authentication():
        groups = []
        roles_marker = request.node.get_closest_marker("roles")
        if roles_marker:
            for group in roles_marker.args:
                groups.append(group)

        user_marker = request.node.get_closest_marker("user")
        if user_marker:
            return User(username=user_marker.args[0], uid=1, groups=groups)

    app.dependency_overrides[get_user_from_session] = override_check_authentication

    yield

    del app.dependency_overrides[get_user_from_session]


@pytest.fixture(scope="function")
def test_client():
    client = TestClient(app)
    yield client


@pytest.fixture(scope="function")
def es_index(request):
    settings = get_settings()
    index_name = settings.ES_INDEX_NAME

    es_container = ElasticSearchContainer(image="elasticsearch:7.14.1")
    es_container.start()

    es_index = get_es_index(
        {
            "host": es_container.get_container_host_ip(),
            "port": es_container.get_exposed_port(9200),
            "ssl": False,
        },
        index_name,
        True,
    )

    def remove_container():
        es_index.close()
        es_container.stop()

    request.addfinalizer(remove_container)

    return es_index

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import traceback

import pytest
import transaction
import webtest
from pyramid.paster import get_appsettings
from pyramid.scripting import prepare
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from georeference import main
from georeference import models
from georeference.utils import create_data_directories

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Make sure to create all test directories when starting the test runner
create_data_directories()


@pytest.fixture(scope='session')
def ini_file():
    # potentially grab this path from a pytest option
    return os.path.join(BASE_PATH, '../testing.ini')


@pytest.fixture(scope='session')
def app_settings(ini_file):
    return get_appsettings(ini_file)


@pytest.fixture(scope='session')
def dbengine(app_settings, ini_file):
    return create_engine(
        app_settings['sqlalchemy.url'],
        encoding='utf8',
        # Set echo=True if te sqlalchemy.url logging output sould be displayed
        echo=False,
    )


@pytest.fixture(scope='session')
def app(app_settings, dbengine):
    try:
        return main({}, dbengine=dbengine, **app_settings)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


@pytest.fixture
def tm():
    tm = transaction.TransactionManager(explicit=True)
    tm.begin()
    tm.doom()

    yield tm

    tm.abort()


@pytest.fixture
def dbsession(app, tm):
    session_factory = app.registry['dbsession_factory']
    return models.get_tm_session(session_factory, tm)


@pytest.fixture
def testapp(app, tm, dbsession):
    # override request.dbsession and request.tm with our own
    # externally-controlled values that are shared across requests but aborted
    # at the end
    testapp = webtest.TestApp(app, extra_environ={
        'HTTP_HOST': 'example.com',
        'tm.active': True,
        'tm.manager': tm,
        'app.dbsession': dbsession,
    })

    return testapp


@pytest.fixture
def app_request(app, tm, dbsession):
    """
    A real request.

    This request is almost identical to a real request but it has some
    drawbacks in tests as it's harder to mock data and is heavier.

    """
    with prepare(registry=app.registry) as env:
        request = env['request']
        request.host = 'example.com'

        # without this, request.dbsession will be joined to the same transaction
        # manager but it will be using a different sqlalchemy.orm.Session using
        # a separate database transaction
        request.dbsession = dbsession
        request.tm = tm

        yield request


@pytest.fixture
def dbsession_only(dbengine):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    Session = sessionmaker(dbengine)
    session = Session()

    Base = declarative_base()
    Base.metadata.bind = dbengine
    Base.metadata.create_all(dbengine)

    yield session

    # automatically close session after usage
    session.close()

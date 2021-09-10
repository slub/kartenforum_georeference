#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import pytest
import transaction
import webtest
from sqlalchemy import create_engine
from pyramid.paster import get_appsettings
from pyramid.scripting import prepare
from georeference import main
from georeference import models

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

@pytest.fixture(scope='session')
def ini_file():
    # potentially grab this path from a pytest option
    return os.path.join(BASE_PATH, '../testing.ini')

@pytest.fixture(scope='session')
def app_settings(ini_file):
    return get_appsettings(ini_file)

@pytest.fixture(scope='session')
def dbengine(app_settings, ini_file):
    return create_engine(app_settings['sqlalchemy.url'], encoding='utf8', echo=True)

@pytest.fixture(scope='session')
def app(app_settings, dbengine):
    return main({}, dbengine=dbengine, **app_settings)

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
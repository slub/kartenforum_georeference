#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
from webtest import Upload

from georeference.settings import ROUTE_PREFIX
from georeference.utils.parser import to_public_map_id

# Necessary for proper testing of the file upload
ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

test_metadata = """{
  "description": "Test",
  "license": "CC-0",
  "map_scale": 1,
  "map_type": "mtb",
  "owner": "Test Owner",
  "time_of_publication": "1923-01-01",
  "title": "Test",
  "title_short": "Test"
}
"""


def test_getMapsById_success_withoutGeorefId(testapp):
    # For clean test setup the test data should also be added to the database within this method
    map_id = to_public_map_id(10003265)

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s' % map_id, status=200)
    assert res.status_int == 200
    assert res.json['map_id'] == map_id
    assert res.json['transformation_id'] is None
    assert res.json["license"] is not None


def test_getMapsById_success_withGeorefId(testapp):
    # For clean test setup the test data should also be added to the database within this method
    map_id = to_public_map_id(10001556)

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s' % map_id, status=200)
    assert res.status_int == 200
    assert res.json['map_id'] == map_id
    assert res.json['transformation_id'] == 11823


def test_getMapsById_badrequest(testapp):
    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps', status=404)
    assert res.status_int == 404


def test_getMapsById_notfound(testapp):
    res = testapp.get(ROUTE_PREFIX + '/maps', status=404)
    assert res.status_int == 404


def test_delete_existing_map(testapp, dbsession):
    res = testapp.delete(ROUTE_PREFIX + '/maps/oai:de:slub-dresden:vk:id-100'
                                        '03265', status=200)

    # First of all rollback session
    dbsession.rollback()

    assert res.status_int == 200


def test_delete_non_existing_map(testapp, dbsession):
    res = testapp.delete(ROUTE_PREFIX + '/maps/oai:de:slub-dresden:vk:id-1', status=400)

    dbsession.rollback()

    assert res.status_int == 400
    assert 'There exists no map with the supplied id' in res.text


def test_delete_invalid_map_id(testapp, dbsession):
    res = testapp.delete(ROUTE_PREFIX + '/maps/oai:de:slub-dresden:vk:id-abcd', status=400)

    dbsession.rollback()

    assert res.status_int == 400
    assert 'Invalid map_id' in res.text


def test_create_new_map_invalid_metadata(testapp):
    infile = os.path.join(os.path.dirname(os.path.realpath(__file__)), './__test_data/test.tif')
    with open(infile, 'rb') as testfile:
        contents = testfile.read()

    data = {
        'metadata': "{}",
        'file': Upload(os.path.basename(infile), contents),
    }

    res = testapp.post('/maps/', data, status=400)

    assert res.status_int == 400
    assert 'Invalid metadata object' in res.text


def test_create_new_map_missing_metadata(testapp):
    infile = os.path.join(os.path.dirname(os.path.realpath(__file__)), './__test_data/test.tif')
    with open(infile, 'rb') as testfile:
        contents = testfile.read()

    data = {
        'file': Upload(os.path.basename(infile), contents),
    }

    res = testapp.post('/maps/', data, status=400)

    assert res.status_int == 400
    assert 'metadata form field is required' in res.text


def test_create_new_map_missing_file(testapp):
    data = {
        'metadata': ''
    }

    res = testapp.post('/maps/', data, status=400)

    assert res.status_int == 400
    assert 'file form field is required' in res.text


def test_create_new_map_invalid_file(testapp, dbsession):
    infile = os.path.join(os.path.dirname(os.path.realpath(__file__)), './__test_data/test.txt')

    with open(infile, 'rb') as testfile:
        contents = testfile.read()

    data = {
        'metadata': test_metadata,
        'file': Upload(os.path.basename(infile), contents),
    }

    res = testapp.post('/maps/', data, status=400)

    dbsession.rollback()

    assert res.status_int == 400
    assert 'Invalid file object' in res.text


def test_create_new_map_successful(testapp, dbsession):
    infile = os.path.join(os.path.dirname(os.path.realpath(__file__)), './__test_data/test.tif')
    with open(infile, 'rb') as testfile:
        contents = testfile.read()

    data = {
        'metadata': test_metadata,
        'file': Upload(os.path.basename(infile), contents),
    }

    res = testapp.post('/maps/', data, status=200)

    dbsession.rollback()

    assert res.status_int == 200
    assert 'map_id' in res.json


def test_update_map_successful_file(testapp, dbsession):
    infile = os.path.join(os.path.dirname(os.path.realpath(__file__)), './__test_data/test.tif')
    map_id = to_public_map_id(10003265)
    with open(infile, 'rb') as testfile:
        contents = testfile.read()

    data = {
        'file': Upload(os.path.basename(infile), contents),
    }

    res = testapp.post(f'/maps/{map_id}', data, status=200)

    dbsession.rollback()

    assert res.status_int == 200
    assert 'map_id' in res.json
    assert res.json['map_id'] == map_id


def test_update_map_successful_metadata(testapp, dbsession):
    map_id = to_public_map_id(10003265)

    data = {
        'metadata': test_metadata
    }

    res = testapp.post(f'/maps/{map_id}', data, status=200)

    dbsession.rollback()

    assert res.status_int == 200
    assert 'map_id' in res.json
    assert res.json['map_id'] == map_id


def test_update_map_missing_file_and_metadata(testapp, dbsession):
    map_id = to_public_map_id(10003265)
    data = {}

    res = testapp.post(f'/maps/{map_id}', data, status=400)

    dbsession.rollback()

    assert res.status_int == 400
    assert 'metadata form field or the file form field is required' in res.text


def test_update_map_invalid_file(testapp, dbsession):
    map_id = to_public_map_id(10003265)
    infile = os.path.join(os.path.dirname(os.path.realpath(__file__)), './__test_data/test.txt')

    with open(infile, 'rb') as testfile:
        contents = testfile.read()

    data = {
        'file': Upload(os.path.basename(infile), contents),
    }

    res = testapp.post(f'/maps/{map_id}', data, status=400)

    dbsession.rollback()

    assert res.status_int == 400
    assert 'Invalid file object' in res.text

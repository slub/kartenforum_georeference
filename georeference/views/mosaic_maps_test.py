#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 21.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from datetime import datetime

from georeference.settings import ROUTE_PREFIX
from georeference.models.jobs import Job, EnumJobType
from georeference.models.mosaic_maps import MosaicMap
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id, from_public_map_id, from_public_mosaic_map_id

test_data = {
    "id": to_public_mosaic_map_id(10),
    "name": "test_name",
    "raw_map_ids": [to_public_map_id(10003265)],
    "title": "Test title",
    "title_short": "Test title_short",
    "time_of_publication": "1923-01-01T00:00:00",
    "link_thumb": "https://link.test.de",
    "map_scale": 25000,
    "last_change": datetime.now().isoformat()
}


def test_GET_mosaic_map_not_found(testapp):
    res = testapp.get(f'{ROUTE_PREFIX}/mosaic_map/{to_public_mosaic_map_id(1111)}', status=404)
    assert res.status_int == 404

def test_GET_mosaic_map_without_empty_fields(testapp, dbsession):
    _insert_test_data(dbsession, [{
        **test_data,
        **{
            "last_service_update": datetime.now().isoformat(),
            "last_overview_update":  datetime.now().isoformat()
        }
    }])

    res = testapp.get(f'{ROUTE_PREFIX}/mosaic_map/{test_data["id"]}', status=200)
    assert res.status_int == 200
    assert res.json['id'] == test_data['id']
    assert res.json['name'] == test_data['name']
    assert res.json['raw_map_ids'][0] == test_data['raw_map_ids'][0]
    assert res.json['time_of_publication'] == test_data['time_of_publication']
    assert res.json['map_scale'] == test_data['map_scale']
    assert res.json['last_change'] == test_data['last_change']
    assert res.json['last_service_update'] is not None
    assert res.json['last_overview_update'] is not None

    dbsession.rollback()


def test_GET_mosaic_map_with_empty_fields(testapp, dbsession):
    _insert_test_data(dbsession, [{
        **test_data,
    }])

    res = testapp.get(f'{ROUTE_PREFIX}/mosaic_map/{test_data["id"]}', status=200)
    assert res.status_int == 200
    assert res.json['id'] == test_data['id']
    assert res.json['last_service_update'] is None
    assert res.json['last_overview_update'] is None

    dbsession.rollback()

def test_GET_mosaic_maps(testapp, dbsession):
    _insert_test_data(dbsession, [{
        **test_data,
        **{
            "last_service_update": datetime.now().isoformat(),
            "last_overview_update":  datetime.now().isoformat()
        }
    }])

    res = testapp.get(f'{ROUTE_PREFIX}/mosaic_maps', status=200)
    assert res.status_int == 200
    assert len(res.json) == 1
    assert res.json[0]['id'] == test_data['id']

    dbsession.rollback()


def test_POST_new_mosaic_map_success(testapp, dbsession):
    data = { **test_data }
    data.pop('id')
    data.pop('last_change')

    res = testapp.post(f'{ROUTE_PREFIX}/mosaic_maps', json.dumps(data), content_type='application/json; charset=utf-8', status=200)
    assert res.status_int == 200
    assert res.json['id'] is not None
    assert res.json['last_change'] is not None
    assert res.json['last_service_update'] is None
    assert res.json['last_overview_update'] is None

    # Check if the jobs was created successfully
    jobs_create = Job.query_not_started_jobs([EnumJobType.MOSAIC_MAP_CREATE.value], dbsession)
    assert len(jobs_create) == 1


def test_POST_new_mosaic_map_failed(testapp):
    data = { **test_data }
    data.pop('id')
    data.pop('last_change')
    data['map_scale'] = '123'

    res = testapp.post(f'{ROUTE_PREFIX}/mosaic_maps', json.dumps(data), content_type='application/json; charset=utf-8', status=400)
    assert res.status_int == 400


def test_POST_update_mosaic_map_success(testapp, dbsession):
    _insert_test_data(dbsession, [{
        **test_data,
    }])
    data = { **test_data }
    data.pop('id')
    data.pop('last_change')
    data['name'] = "test"

    res = testapp.post(f'{ROUTE_PREFIX}/mosaic_map/{test_data["id"]}', json.dumps(data), content_type='application/json; charset=utf-8', status=200)
    assert res.status_int == 200
    assert res.json['id'] == test_data["id"]
    assert res.json['last_change'] != test_data['last_change']
    assert res.json['name'] == data['name']

    # Check also if the database was updated correctly
    mosaic_map_obj = MosaicMap.by_id(from_public_mosaic_map_id(test_data['id']), dbsession)
    assert mosaic_map_obj.name == data['name']

    # Check if the jobs was created successfully
    jobs_create = Job.query_not_started_jobs([EnumJobType.MOSAIC_MAP_CREATE.value], dbsession)
    assert len(jobs_create) == 1

    dbsession.rollback()


def test_POST_refresh_mosaic_map_success(testapp, dbsession):
    _insert_test_data(dbsession, [{
        **test_data,
    }])
    data = { **test_data }
    data.pop('id')
    data.pop('last_change')

    res = testapp.post(f'{ROUTE_PREFIX}/mosaic_map/{test_data["id"]}/refresh', status=200)
    assert res.status_int == 200
    assert res.json['status'] == 'ok'

    # Check if the jobs was created successfully
    jobs_create = Job.query_not_started_jobs([EnumJobType.MOSAIC_MAP_CREATE.value], dbsession)
    assert len(jobs_create) == 1

    dbsession.rollback()


def test_DELETE_mosaic_map_success(testapp, dbsession):
    _insert_test_data(dbsession, [{
        **test_data,
    }])

    res = testapp.delete(f'{ROUTE_PREFIX}/mosaic_map/{test_data["id"]}', status=200)
    assert res.status_int == 200
    assert res.json['status'] == 'ok'

    # Check also if the mosaic_map was removed from the database
    mosaic_map_obj = MosaicMap.by_id(from_public_mosaic_map_id(test_data['id']), dbsession)
    assert mosaic_map_obj is None

    # Check if the jobs was created successfully
    jobs_create = Job.query_not_started_jobs([EnumJobType.MOSAIC_MAP_DELETE.value], dbsession)
    assert len(jobs_create) == 1

    dbsession.rollback()


def test_DELETE_mosaic_map_failed_notfound(testapp, dbsession):
    res = testapp.delete(f'{ROUTE_PREFIX}/mosaic_map/{to_public_mosaic_map_id(121212)}', status=404)
    assert res.status_int == 404


def _insert_test_data(dbsession, test_data):
    for rec in test_data:
        dbsession.add(
            MosaicMap(
                id=from_public_mosaic_map_id(rec["id"]),
                name=rec["name"],
                raw_map_ids=map(lambda x: from_public_map_id(x), rec["raw_map_ids"]),
                title=rec["title"],
                title_short=rec["title_short"],
                time_of_publication=rec["time_of_publication"],
                link_thumb=rec["link_thumb"],
                map_scale=rec["map_scale"],
                last_change=rec["last_change"],
                last_service_update=rec["last_service_update"] if "last_service_update" in rec else None,
                last_overview_update=rec["last_overview_update"] if "last_overview_update" in rec else None,
            )
        )

    dbsession.flush()
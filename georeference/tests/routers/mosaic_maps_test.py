#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime

import pytest
from sqlmodel import Session

from georeference.models.enums import EnumJobType
from georeference.models.job import Job
from georeference.models.mosaic_map import MosaicMap
# Created by nicolas.looschen@pikobytes.de on 25.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from georeference.utils.parser import (
    to_public_mosaic_map_id,
    to_public_map_id,
    from_public_mosaic_map_id,
    from_public_map_id,
)

test_data = {
    "id": to_public_mosaic_map_id(10),
    "name": "test_name",
    "description": "testtest",
    "raw_map_ids": [to_public_map_id(10003265)],
    "title": "Test title",
    "title_short": "Test title_short",
    "time_of_publication": "1923-01-01T00:00:00",
    "link_thumb": "https://link.test.de",
    "map_scale": 25000,
    "last_change": datetime.now().isoformat(),
}


class TestMosaicMapsGet:
    def test_get_mosaic_map_not_found(
        self, test_client, override_get_session_read_only
    ):
        res = test_client.get(f"/mosaic_maps/{to_public_mosaic_map_id(1111)}")
        assert res.status_code == 404

    def test_get_mosaic_map_without_empty_fields(
        self, test_client, override_get_session, db_container
    ):
        with Session(db_container[1]) as session:
            _insert_test_data(
                session,
                [
                    {
                        **test_data,
                        **{
                            "last_service_update": datetime.now().isoformat(),
                            "last_overview_update": datetime.now().isoformat(),
                        },
                    }
                ],
            )

        res = test_client.get(f"/mosaic_maps/{test_data["id"]}")
        assert res.status_code == 200

        result = res.json()
        assert result["id"] == test_data["id"]
        assert result["name"] == test_data["name"]
        assert result["raw_map_ids"][0] == test_data["raw_map_ids"][0]
        assert result["time_of_publication"] == test_data["time_of_publication"]
        assert result["map_scale"] == test_data["map_scale"]
        assert result["description"] == test_data["description"]
        assert result["last_change"] == test_data["last_change"]
        assert result["last_service_update"] is not None
        assert result["last_overview_update"] is not None

    def test_get_mosaic_map_with_empty_fields(
        self, test_client, override_get_session, db_container
    ):
        with Session(db_container[1]) as session:
            _insert_test_data(
                session,
                [
                    {
                        **test_data,
                    }
                ],
            )

        res = test_client.get(f"/mosaic_maps/{test_data["id"]}")

        assert res.status_code == 200
        result = res.json()
        assert result["id"] == test_data["id"]
        assert result["last_service_update"] is None
        assert result["last_overview_update"] is None

    def test_get_mosaic_maps(self, test_client, db_container, override_get_session):
        with Session(db_container[1]) as session:
            _insert_test_data(
                session,
                [
                    {
                        **test_data,
                        **{
                            "last_service_update": datetime.now().isoformat(),
                            "last_overview_update": datetime.now().isoformat(),
                        },
                    }
                ],
            )

        res = test_client.get("/mosaic_maps")
        assert res.status_code == 200
        result = res.json()
        assert len(result) == 1
        assert result[0]["id"] == test_data["id"]


def _insert_test_data(session: Session, test_data):
    for rec in test_data:
        session.add(
            MosaicMap(
                id=from_public_mosaic_map_id(rec["id"]),
                name=rec["name"],
                raw_map_ids=map(lambda x: from_public_map_id(x), rec["raw_map_ids"]),
                title=rec["title"],
                title_short=rec["title_short"],
                description=rec["description"],
                time_of_publication=rec["time_of_publication"],
                link_thumb=rec["link_thumb"],
                map_scale=rec["map_scale"],
                last_change=rec["last_change"],
                last_service_update=rec["last_service_update"]
                if "last_service_update" in rec
                else None,
                last_overview_update=rec["last_overview_update"]
                if "last_overview_update" in rec
                else None,
            )
        )

    session.commit()


class TestMapDelete:
    def test_delete_mosaic_map_unauthenticated(
        self, test_client, override_get_session_read_only
    ):
        res = test_client.delete(f"/mosaic_maps/{test_data["id"]}")
        assert res.status_code == 401

    @pytest.mark.user("test")
    def test_delete_mosaic_map_unauthorized(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.delete(f"/mosaic_maps/{test_data["id"]}")
        assert res.status_code == 403

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_delete_mosaic_map_success(
        self,
        test_client,
        db_container,
        override_get_session,
        override_get_user_from_session,
    ):
        with Session(db_container[1]) as session:
            _insert_test_data(
                session,
                [
                    {
                        **test_data,
                    }
                ],
            )

        res = test_client.delete(f'/mosaic_maps/{test_data["id"]}')
        assert res.status_code == 200
        result = res.json()
        assert result["mosaic_map_id"] == test_data["id"]

        # Check also if the mosaic_map was removed from the database
        mosaic_map_obj = MosaicMap.by_public_id(test_data["id"], session)
        assert mosaic_map_obj is None

        # Check if the jobs was created successfully
        jobs_delete = Job.query_not_started_jobs(
            [EnumJobType.MOSAIC_MAP_DELETE.value], session
        )
        assert len(jobs_delete) == 1

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_delete_mosaic_map_failed_notfound(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.delete(f"/mosaic_maps/{to_public_mosaic_map_id(121212)}")
        assert res.status_code == 404


class TestMosaicMapCreate:
    def test_post_mosaic_map_unauthenticated(
        self, test_client, override_get_session_read_only
    ):
        res = test_client.post("/mosaic_maps")
        assert res.status_code == 401

    @pytest.mark.user("test")
    def test_post_mosaic_map_unauthorized(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.post("/mosaic_maps")
        assert res.status_code == 403

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_post_new_mosaic_map_success(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
        db_container,
    ):
        data = {**test_data}
        data.pop("id")
        data.pop("last_change")

        res = test_client.post(
            "/mosaic_maps",
            content=json.dumps(data),
        )
        assert res.status_code == 200
        result = res.json()

        assert result["id"] is not None
        assert result["last_change"] is not None
        assert result["last_service_update"] is None
        assert result["last_overview_update"] is None

        with Session(db_container[1]) as session:
            # Check if the jobs was created successfully
            jobs_create = Job.query_not_started_jobs(
                [EnumJobType.MOSAIC_MAP_CREATE.value], session
            )
            assert len(jobs_create) == 1

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_post_new_mosaic_map_failed(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
        db_container,
    ):
        data = {**test_data}
        data.pop("id")
        data.pop("last_change")
        data["map_scale"] = "abc"

        res = test_client.post(
            "/mosaic_maps",
            content=json.dumps(data),
        )
        assert res.status_code == 422


class TestMosaicMapUpdate:
    def test_post_mosaic_map_update_unauthenticated(
        self, test_client, override_get_session_read_only
    ):
        res = test_client.post(f"/mosaic_maps/{test_data['id']}")
        assert res.status_code == 401

    @pytest.mark.user("test")
    def test_post_mosaic_map_update_unauthorized(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.post(f"/mosaic_maps/{test_data['id']}")
        assert res.status_code == 403

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_post_update_mosaic_map_success(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
        db_container,
    ):
        with Session(db_container[1]) as session:
            _insert_test_data(
                session,
                [
                    {
                        **test_data,
                    }
                ],
            )
        data = {**test_data}
        data.pop("id")
        data.pop("last_change")
        data["name"] = "test"

        res = test_client.post(
            f'/mosaic_maps/{test_data["id"]}', content=json.dumps(data)
        )

        assert res.status_code == 200
        result = res.json()

        assert result["id"] == test_data["id"]
        assert result["last_change"] != test_data["last_change"]
        assert result["name"] == data["name"]

        with Session(db_container[1]) as session:
            # Check also if the database was updated correctly
            mosaic_map_obj = MosaicMap.by_id(
                from_public_mosaic_map_id(test_data["id"]), session
            )
            assert mosaic_map_obj.name == data["name"]

            # Check if the jobs was created successfully
            jobs_create = Job.query_not_started_jobs(
                [EnumJobType.MOSAIC_MAP_CREATE.value], session
            )
            assert len(jobs_create) == 1


class TestMosaicMapRefresh:
    def test_post_mosaic_map_update_unauthenticated(
        self, test_client, override_get_session_read_only
    ):
        res = test_client.post(f'/mosaic_maps/{test_data["id"]}/refresh')
        assert res.status_code == 401

    @pytest.mark.user("test")
    def test_post_mosaic_map_update_unauthorized(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.post(f'/mosaic_maps/{test_data["id"]}/refresh')
        assert res.status_code == 403

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_post_refresh_mosaic_map_success(
        self,
        test_client,
        db_container,
        override_get_session,
        override_get_user_from_session,
    ):
        with Session(db_container[1]) as session:
            _insert_test_data(
                session,
                [
                    {
                        **test_data,
                    }
                ],
            )

        data = {**test_data}
        data.pop("id")
        data.pop("last_change")

        res = test_client.post(f'/mosaic_maps/{test_data["id"]}/refresh')
        assert res.status_code == 200
        result = res.json()
        assert result["mosaic_map_id"] == test_data["id"]
        assert result["message"] == "Mosaic map scheduled for refresh."

        with Session(db_container[1]) as session:
            # Check if the jobs was created successfully
            jobs_create = Job.query_not_started_jobs(
                [EnumJobType.MOSAIC_MAP_CREATE.value], session
            )
            assert len(jobs_create) == 1

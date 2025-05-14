#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 02.05.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

import pytest
from sqlmodel import Session
from starlette.testclient import TestClient
from georeference.models.vector_map_external import VectorMapExternal
from georeference.tests.routers.__test_data.vector_maps_external import (
    valid_vector_map,
    invalid_vector_map,
    invalid_vector_maps_time_period,
)


class TestCreateVectorMapExternal:
    def test_create_vector_map_fail_not_authenticated(
        self,
        test_client: TestClient,
    ):
        response = test_client.post("/vector_maps_external", json=valid_vector_map)
        assert response.status_code == 401

    @pytest.mark.user("user_1")
    def test_create_vector_map_fail_not_authorized(
        self,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post("/vector_maps_external", json=valid_vector_map)
        assert response.status_code == 403

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_create_vector_map_fail_invalid_geojson(
        self,
        test_client: TestClient,
        override_get_session_read_only,
        override_get_user_from_session,
        override_get_http_client_with_invalid_response,
    ):
        response = test_client.post("/vector_maps_external", json=valid_vector_map)
        assert response.status_code == 422

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_create_vector_map_fail_missing_properties(
        self,
        test_client: TestClient,
        override_get_session_read_only,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
    ):
        response = test_client.post("/vector_maps_external", json=invalid_vector_map)
        assert response.status_code == 422

        missing_props = [
            error["loc"][1]
            for error in response.json()["detail"]
            if error["type"] == "missing"
        ]

        assert "title" in missing_props
        assert "link_content" in missing_props
        assert "time_period" in missing_props

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    @pytest.mark.parametrize(
        "invalid_vector_map,expected_error", invalid_vector_maps_time_period
    )
    def test_create_vector_map_fail_invalid_time_period(
        self,
        invalid_vector_map,
        expected_error,
        test_client: TestClient,
        override_get_session_read_only,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
    ):
        response = test_client.post("/vector_maps_external", json=invalid_vector_map)

        assert response.status_code == 422
        assert len(response.json()["detail"]) == 1
        assert response.json()["detail"][0]["type"] == expected_error

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_create_vector_map_success(
        self,
        test_client: TestClient,
        db_container,
        override_get_session,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
        override_get_async_es_index,
    ):
        response = test_client.post("/vector_maps_external", json=valid_vector_map)
        assert response.status_code == 201

        data = response.json()
        assert data["id"] is not None

        with Session(db_container[1]) as session:
            assert VectorMapExternal.by_public_id(data["id"], session) is not None


class TestReadVectorMapExternal:
    def test_read_vector_map_not_authenticated(
        self,
        test_client: TestClient,
    ):
        response = test_client.get("/vector_maps_external/fake-id")
        assert response.status_code == 401

    @pytest.mark.user("user_1")
    def test_read_vector_map_not_authorized(
        self,
        override_get_user_from_session,
        test_client: TestClient,
    ):
        response = test_client.get("/vector_maps_external/fake-id")
        assert response.status_code == 403

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_read_vector_map_success(
        self,
        test_client: TestClient,
        override_get_session,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
        override_get_async_es_index,
    ):
        response1 = test_client.post("/vector_maps_external", json=valid_vector_map)
        response1_id = response1.json()["id"]
        response2 = test_client.get(
            "/vector_maps_external/{id}".format(id=response1_id)
        )

        assert response2.status_code == 200
        assert response2.json()["id"] == response1_id


class TestUpdateVectorMapExternal:
    def test_fail_update_vector_map_not_authenticated(
        self,
        test_client: TestClient,
    ):
        response = test_client.put(
            "/vector_maps_external/fake-id", json=valid_vector_map
        )
        assert response.status_code == 401

    @pytest.mark.user("user_1")
    def test_fail_update_vector_map_not_authorized(
        self,
        override_get_user_from_session,
        test_client: TestClient,
    ):
        response = test_client.put(
            "/vector_maps_external/fake-id", json=valid_vector_map
        )
        assert response.status_code == 403

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_update_vector_map_fail_missing_properties(
        self,
        test_client: TestClient,
        provision_mock_vector_map_external,
        override_get_session,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
    ):
        vector_map = provision_mock_vector_map_external
        id_ = vector_map.public_id

        response = test_client.put(
            "/vector_maps_external/{id}".format(id=id_), json=invalid_vector_map
        )
        assert response.status_code == 422

        missing_props = [
            error["loc"][1]
            for error in response.json()["detail"]
            if error["type"] == "missing"
        ]

        assert "title" in missing_props
        assert "link_content" in missing_props
        assert "time_period" in missing_props

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    @pytest.mark.parametrize(
        "invalid_vector_map,expected_error", invalid_vector_maps_time_period
    )
    def test_update_vector_map_fail_invalid_time_period(
        self,
        invalid_vector_map,
        expected_error,
        provision_mock_vector_map_external,
        test_client: TestClient,
        override_get_session_read_only,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
    ):
        vector_map = provision_mock_vector_map_external
        id_ = vector_map.public_id
        response = test_client.put(
            "/vector_maps_external/{id}".format(id=id_), json=invalid_vector_map
        )

        assert response.status_code == 422
        assert len(response.json()["detail"]) == 1
        assert response.json()["detail"][0]["type"] == expected_error

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_success_update_vector_map(
        self,
        db_container,
        provision_mock_vector_map_external,
        override_get_session,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
        override_get_async_es_index,
    ):
        vector_map = provision_mock_vector_map_external
        valid_vector_map["title"] = "Changed"
        update_response = test_client.put(
            "/vector_maps_external/{id}".format(id=vector_map.public_id),
            json=valid_vector_map,
        )

        assert update_response.status_code == 200

        update_data = update_response.json()
        assert update_data["id"] == str(vector_map.public_id)
        assert update_data["title"] == "Changed"

        with Session(db_container[1]) as session:
            vector_map = VectorMapExternal.by_public_id(vector_map.public_id, session)

            assert vector_map.title == "Changed"
            assert vector_map.description == valid_vector_map["description"]


class TestDeleteVectorMapExternal:
    def test_fail_delete_vector_map_not_authenticated(
        self,
        test_client: TestClient,
    ):
        response = test_client.delete("/vector_maps_external/fake-id")
        assert response.status_code == 401

    @pytest.mark.user("user_1")
    def test_fail_delete_vector_map_not_authorized(
        self,
        override_get_user_from_session,
        test_client: TestClient,
    ):
        response = test_client.delete("/vector_maps_external/fake-id")
        assert response.status_code == 403

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_success_delete_vector_map(
        self,
        db_container,
        provision_mock_vector_map_external,
        override_get_session,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
    ):
        vector_map = provision_mock_vector_map_external
        delete_response = test_client.delete(
            "/vector_maps_external/{id}".format(id=str(vector_map.public_id))
        )

        delete_data = delete_response.json()
        assert delete_response.status_code == 200
        assert delete_data["id"] == str(vector_map.public_id)

        with Session(db_container[1]) as session:
            vector_map = VectorMapExternal.by_public_id(vector_map.public_id, session)

            assert vector_map is None


class TestRefreshVectorMapExternal:
    def test_fail_refresh_vector_map_not_authenticated(
        self,
        test_client: TestClient,
    ):
        response = test_client.post(
            "/vector_maps_external/refresh_search_index/fake-id"
        )
        assert response.status_code == 401

    @pytest.mark.user("user_1")
    def test_fail_refresh_vector_map_not_authorized(
        self,
        override_get_user_from_session,
        test_client: TestClient,
    ):
        response = test_client.post(
            "/vector_maps_external/refresh_search_index/fake-id"
        )
        assert response.status_code == 403

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_fail_refresh_vector_map_invalidgeojson(
        self,
        db_container,
        provision_mock_vector_map_external,
        override_get_session,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_http_client_with_invalid_response,
    ):
        vector_map = provision_mock_vector_map_external
        response = test_client.post(
            "/vector_maps_external/refresh_search_index/{id}".format(
                id=str(vector_map.public_id)
            )
        )

        assert response.status_code == 422

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_success_refresh_vector_map(
        self,
        db_container,
        provision_mock_vector_map_external,
        override_get_session,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_http_client_with_valid_response,
    ):
        vector_map = provision_mock_vector_map_external
        response = test_client.post(
            "/vector_maps_external/refresh_search_index/{id}".format(
                id=str(vector_map.public_id)
            )
        )

        assert response.status_code == 204

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 12.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import pytest
from sqlmodel import Session
from starlette.testclient import TestClient

from georeference.models.vector_map import VectorMap, VectorMapRoles
from georeference.tests.routers.__test_data.vector_maps import (
    vector_map_with_empty_feature_collection,
    vector_map_updated_metadata,
    empty_feature_collection,
    vector_map_patch_payload_with_metadata,
    vector_map_patch_payload_without_metadata,
    vector_map_with_point,
)


class TestCreateVectorMap:
    def test_create_vector_map_fail_not_authenticated(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps", json=vector_map_with_empty_feature_collection
        )
        assert response.status_code == 401

    @pytest.mark.user("user_1")
    def test_create_vector_map_fail_not_authorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps", json=vector_map_with_empty_feature_collection
        )
        assert response.status_code == 403

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_create_vector_map_success_editor(
        self,
        override_get_session,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_async_es_index,
    ):
        response = test_client.post(
            "/vector_maps", json=vector_map_with_empty_feature_collection
        )
        assert response.status_code == 201

        data = response.json()
        assert data["id"] is not None

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_create_vector_map_success_admin(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_async_es_index,
    ):
        response = test_client.post(
            "/vector_maps", json=vector_map_with_empty_feature_collection
        )
        assert response.status_code == 201

        data = response.json()
        assert data["id"] is not None

        with Session(db_container[1]) as session:
            assert VectorMap.by_public_id(data["id"], session) is not None

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_create_vector_map_success_admin_with_point(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_async_es_index,
    ):
        response = test_client.post("/vector_maps", json=vector_map_with_point)
        assert response.status_code == 201

        data = response.json()
        assert data["id"] is not None

        with Session(db_container[1]) as session:
            assert VectorMap.by_public_id(data["id"], session) is not None


class TestReadVectorMap:
    def test_get_vector_map_without_role(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.get("/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032")
        assert response.status_code == 200

        data = response.json()

        assert data["title"] == "Dresden"
        assert "user_role" not in data
        assert "version" not in data
        assert data["id"] == "7d06b85a-99b4-404a-9501-a282e0180032"

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_get_vector_map_with_role_owner(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get("/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032")

        assert response.status_code == 200

        data = response.json()

        assert data["title"] == "Dresden"
        assert data["user_role"] == "owner"
        assert data["version"] == 0
        assert data["id"] == "7d06b85a-99b4-404a-9501-a282e0180032"

    @pytest.mark.user("test_user_2")
    @pytest.mark.roles("vk2-editor")
    def test_get_vector_map_with_role_editor(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get("/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032")

        assert response.status_code == 200

        data = response.json()

        assert data["title"] == "Dresden"
        assert data["user_role"] == "editor"
        assert data["version"] == 0
        assert data["id"] == "7d06b85a-99b4-404a-9501-a282e0180032"

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_get_vector_map_admin(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get("/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032")

        assert response.status_code == 200

        data = response.json()

        assert data["title"] == "Dresden"
        assert data["user_role"] == "owner"
        assert data["version"] == 0
        assert data["id"] == "7d06b85a-99b4-404a-9501-a282e0180032"

    def test_get_vector_map_correct_version_content(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.get("/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7")

        assert response.status_code == 200

        data = response.json()

        # In version 0 there is one feature, in version 1 there are two features
        assert len(data["geojson"]["features"]) == 2

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-admin")
    def test_get_vector_map_correct_version(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get("/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7")

        assert response.status_code == 200

        data = response.json()

        assert data["title"] == "Test Map"
        assert data["id"] == "8d2605e2-1ecd-47d7-be2c-9fb3042715c7"
        assert data["version"] == 1
        assert data["user_role"] == "owner"

    @pytest.mark.user("test_user_2")
    @pytest.mark.roles("vk2-editor")
    def test_get_vector_map_no_authorization(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get("/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7")

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == "8d2605e2-1ecd-47d7-be2c-9fb3042715c7"
        assert "user_role" not in data
        assert "version" not in data


class TestUpdateVectorMapMetadata:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.put(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
            json=vector_map_updated_metadata,
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.put(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
            json=vector_map_updated_metadata,
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_update_vector_map_success(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.put(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
            json=vector_map_updated_metadata,
        )

        assert response.status_code == 200

        with Session(db_container[1]) as session:
            vector_map = VectorMap.by_public_id(
                "8d2605e2-1ecd-47d7-be2c-9fb3042715c7", session
            )

            assert vector_map.title == vector_map_updated_metadata["title"]
            assert vector_map.description == vector_map_updated_metadata["description"]


class TestUpdateVectorMap:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.patch(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
            json=vector_map_patch_payload_with_metadata,
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.patch(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
            json=vector_map_patch_payload_with_metadata,
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user_2")
    @pytest.mark.roles("vk2-editor")
    def test_editor_unauthorized_for_metadata(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        vector_data = test_client.get(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032",
        )

        assert vector_data.json()["user_role"] == "editor"

        response = test_client.patch(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032",
            json=vector_map_patch_payload_with_metadata,
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user_2")
    @pytest.mark.roles("vk2-editor")
    def test_editor_authorized_for_geojson(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_async_es_index,
    ):
        vector_data = test_client.get(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032",
        )

        assert vector_data.json()["user_role"] == "editor"

        response = test_client.patch(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032",
            json=vector_map_patch_payload_without_metadata,
        )

        assert response.status_code == 200

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_update_vector_map_success(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_async_es_index,
    ):
        response = test_client.patch(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
            json=vector_map_patch_payload_with_metadata,
        )

        assert response.status_code == 200

        with Session(db_container[1]) as session:
            vector_map = VectorMap.by_public_id(
                "8d2605e2-1ecd-47d7-be2c-9fb3042715c7", session
            )

            assert vector_map.title == vector_map_updated_metadata["title"]
            assert vector_map.description == vector_map_updated_metadata["description"]


class TestDeleteVectorMap:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.delete(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.delete(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_delete_vector_map_success(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.delete(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7",
        )

        assert response.status_code == 200

        with Session(db_container[1]) as session:
            vector_map = VectorMap.by_public_id(
                "8d2605e2-1ecd-47d7-be2c-9fb3042715c7", session
            )

            assert vector_map is None


class TestVectorMapReadVersions:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions",
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions",
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_get_versions_success(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions",
        )

        assert response.status_code == 200
        assert len(response.json()) == 2


class TestVectorMapReadVersion:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions/0",
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions/0",
        )

        assert response.status_code == 404

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_get_version_success(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions/0",
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data["geojson"]["features"]) == 1
        assert data["version"] == 0
        assert "submitted" in data

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_get_version_1_success(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions/1",
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data["geojson"]["features"]) == 2
        assert data["version"] == 1
        assert "submitted" in data


class TestCreateVectorMapVersion:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions",
            json=empty_feature_collection,
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions",
            json={"geojson": empty_feature_collection, "current_version": 1},
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_create_new_version_invalid_current_version(
        self,
        override_get_session_read_only,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions",
            json={"geojson": empty_feature_collection, "current_version": 15},
        )

        assert response.status_code == 409

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_create_new_version_success(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
        override_get_async_es_index,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/versions",
            json={"geojson": empty_feature_collection, "current_version": 1},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["version"] == 2

        with Session(db_container[1]) as session:
            vector_map, vector_map_content = VectorMap.by_public_id_with_contents(
                "8d2605e2-1ecd-47d7-be2c-9fb3042715c7", session
            )

            assert len(vector_map_content.content["features"]) == 0


class TestVectorMapRolesRead:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles",
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles",
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_get_roles_success(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.get(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles",
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1


class TestVectorMapRolesAdd:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles/add",
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles/add",
            json={"user_id": "test_user_2", "role": "editor"},
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_add_role_success(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles/add",
            json={"user_id": "test_user_2", "role": "editor"},
        )

        assert response.status_code == 200

        with Session(db_container[1]) as session:
            vector_map = VectorMap.by_public_id(
                "8d2605e2-1ecd-47d7-be2c-9fb3042715c7", session
            )
            roles = VectorMapRoles.by_vector_map_id(vector_map.id, session)

            assert len(roles) == 2

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_add_role_failure_existing_role(
        self,
        override_get_session_read_only,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles/add",
            json={"user_id": "test_user", "role": "editor"},
        )

        assert response.status_code == 409

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_add_role_failure_unauthorized(
        self,
        override_get_session_read_only,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles/add",
            json={"user_id": "new_user", "role": "owner"},
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-admin")
    def test_add_role_owner_success_admin(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/8d2605e2-1ecd-47d7-be2c-9fb3042715c7/roles/add",
            json={"user_id": "new_user", "role": "owner"},
        )

        assert response.status_code == 200

        with Session(db_container[1]) as session:
            vector_map = VectorMap.by_public_id(
                "8d2605e2-1ecd-47d7-be2c-9fb3042715c7", session
            )
            roles = VectorMapRoles.by_vector_map_id(vector_map.id, session)

            assert len(roles) == 2


class TestVectorMapRolesRemove:
    def test_no_user_authentication(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.post(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032/roles/remove",
        )

        assert response.status_code == 401

    @pytest.mark.user("user_1")
    @pytest.mark.roles("vk2-editor")
    def test_user_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032/roles/remove",
            json={"user_id": "test_user"},
        )

        assert response.status_code == 403

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_remove_role_success(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032/roles/remove",
            json={"user_id": "test_user_2"},
        )

        assert response.status_code == 200

        with Session(db_container[1]) as session:
            vector_map = VectorMap.by_public_id(
                "7d06b85a-99b4-404a-9501-a282e0180032", session
            )
            roles = VectorMapRoles.by_vector_map_id(vector_map.id, session)
            assert len(roles) == 1

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_remove_role_failure_not_found(
        self,
        override_get_session_read_only,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032/roles/remove",
            json={"user_id": "new_user"},
        )

        assert response.status_code == 404

    @pytest.mark.user("test_user")
    @pytest.mark.roles("vk2-editor")
    def test_remove_role_failure_not_authorized(
        self,
        override_get_session_read_only,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/vector_maps/7d06b85a-99b4-404a-9501-a282e0180032/roles/remove",
            json={"user_id": "test_user"},
        )

        assert response.status_code == 403

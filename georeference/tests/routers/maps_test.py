#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import pytest

from georeference.utils.parser import to_public_map_id

# Created by nicolas.looschen@pikobytes.de on 24.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

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


class TestMapsGet:
    def test_get_maps_by_id_success_without_georef_id(
        self, test_client, override_get_session_read_only
    ):
        map_id = to_public_map_id(10003265)
        res = test_client.get(f"/maps/{map_id}")

        assert res.status_code == 200
        response = res.json()
        assert response["map_id"] == map_id
        assert response["transformation_id"] is None
        assert response["license"] is not None

    def test_get_maps_by_id_success_with_georef_id(
        self, test_client, override_get_session_read_only
    ):
        map_id = to_public_map_id(10001556)
        res = test_client.get(f"/maps/{map_id}")

        assert res.status_code == 200
        response = res.json()
        assert response["map_id"] == map_id
        assert response["transformation_id"] == 11823

    def test_get_maps_by_id_non_existing_id(
        self, test_client, override_get_session_read_only
    ):
        map_id = to_public_map_id(101)
        res = test_client.get(f"/maps/{map_id}")

        assert res.status_code == 404


class TestMapsDelete:
    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_delete_maps_by_id_logged_in(
        self, test_client, override_get_session, override_get_user_from_session
    ):
        map_id = to_public_map_id(10003265)
        res = test_client.delete(f"/maps/{map_id}")

        assert res.status_code == 200
        response = res.json()
        assert response["map_id"] == map_id

    def test_delete_maps_by_id_not_logged_in(
        self, test_client, override_get_session_read_only
    ):
        map_id = to_public_map_id(10003265)
        res = test_client.delete(f"/maps/{map_id}")

        assert res.status_code == 401

    @pytest.mark.user("test")
    def test_delete_maps_by_id_not_authorized(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        map_id = to_public_map_id(10003265)
        res = test_client.delete(f"/maps/{map_id}")

        assert res.status_code == 403
        response = res.json()
        assert response["detail"] == "Not authorized"


class TestMapsUpdate:
    def test_update_map_not_logged_in(
        self, test_client, override_get_session_read_only
    ):
        map_id = to_public_map_id(10003265)
        res = test_client.post(f"/maps/{map_id}")

        assert res.status_code == 401

    @pytest.mark.user("test")
    def test_update_map_not_authorized(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        map_id = to_public_map_id(10003265)
        res = test_client.post(f"/maps/{map_id}")

        assert res.status_code == 403

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_update_map_successful_file(
        self, test_client, override_get_session, override_get_user_from_session
    ):
        infile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "./__test_data/test.tif"
        )
        map_id = to_public_map_id(10003265)
        with open(infile, "rb") as testfile:
            contents = testfile.read()

        data = {
            "file": (os.path.basename(infile), contents, "image/tiff"),
        }

        res = test_client.post(f"/maps/{map_id}", files=data)

        assert res.status_code == 200
        response = res.json()
        assert response["map_id"] == map_id

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_update_map_successful_metadata(
        self, test_client, override_get_session, override_get_user_from_session
    ):
        map_id = to_public_map_id(10003265)

        data = {"metadata": test_metadata}

        res = test_client.post(
            f"/maps/{map_id}",
            data=data,
            # This makes fastapi treat this as multipart form data, our endpoints just ignores the file
            files={"test": (os.path.basename(__file__), b"test", "image/tiff")},
        )

        assert res.status_code == 200
        result = res.json()
        assert result["map_id"] == map_id

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_update_map_missing_file_and_metadata(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        map_id = to_public_map_id(10003265)
        data = {"test": (os.path.basename(__file__), b"test", "image/tiff")}

        res = test_client.post(f"/maps/{map_id}", files=data)

        assert res.status_code == 400
        result = res.json()
        assert result["detail"] == "No metadata or file was provided."

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_update_map_invalid_file(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        map_id = to_public_map_id(10003265)
        infile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "./__test_data/test.txt"
        )

        with open(infile, "rb") as testfile:
            contents = testfile.read()

        data = {
            "file": (os.path.basename(infile), contents, "image/tiff"),
        }

        res = test_client.post(f"/maps/{map_id}", files=data)

        assert res.status_code == 400
        result = res.json()
        assert result["detail"] == "Invalid file object at POST request."


class TestMapCreate:
    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_create_new_map_invalid_metadata(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        infile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "./__test_data/test.tif"
        )
        with open(infile, "rb") as testfile:
            contents = testfile.read()

        data = {
            "metadata": "{'test': 1234}",
        }

        files = {
            "file": (os.path.basename(infile), contents, "image/tiff"),
        }

        res = test_client.post("/maps/", data=data, files=files)

        assert res.status_code == 400
        result = res.json()
        assert result["detail"] == "Invalid metadata provided."

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_create_new_map_missing_metadata(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        infile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "./__test_data/test.tif"
        )
        with open(infile, "rb") as testfile:
            contents = testfile.read()

        files = {
            "file": (os.path.basename(infile), contents, "image/tiff"),
        }

        res = test_client.post("/maps/", files=files)

        assert res.status_code == 400
        result = res.json()
        assert result["detail"] == "The metadata form field is required."

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_create_new_map_missing_file(
        self,
        test_client,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        data = {"metadata": "{}"}

        res = test_client.post(
            "/maps/",
            data=data,
            files={"test": (os.path.basename(__file__), b"test", "image/tiff")},
        )

        assert res.status_code == 400
        result = res.json()
        assert result["detail"] == "The file form field is required."

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_create_new_map_invalid_file(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
    ):
        infile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "./__test_data/test.txt"
        )

        with open(infile, "rb") as testfile:
            contents = testfile.read()

        data = {
            "metadata": test_metadata,
        }

        files = {
            "file": (os.path.basename(infile), contents, "image/tiff"),
        }

        res = test_client.post("/maps/", files=files, data=data)

        assert res.status_code == 400
        result = res.json()
        assert result["detail"] == "Invalid file object at POST request."

    @pytest.mark.user("test")
    @pytest.mark.roles("vk2-admin")
    def test_create_new_map_successful(
        self,
        test_client,
        override_get_session,
        override_get_user_from_session,
    ):
        infile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "./__test_data/test.tif"
        )

        with open(infile, "rb") as testfile:
            contents = testfile.read()

        data = {
            "metadata": test_metadata,
        }

        files = {
            "file": (os.path.basename(infile), contents, "image/tiff"),
        }

        res = test_client.post("/maps/", files=files, data=data)

        assert res.status_code == 200
        result = res.json()
        assert "map_id" in result
        assert result["map_id"].startswith("oai:de:slub-dresden:vk:id-")

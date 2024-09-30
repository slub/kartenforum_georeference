#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from georeference.models.map_view import MapView


class TestMapView:
    def test_get_map_view(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
    ):
        with Session(db_container[1]) as session:
            session.add(
                MapView(
                    id=1,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    public_id="test_view",
                    map_view_json="",
                    request_count=0,
                    last_request=datetime.now().isoformat(),
                )
            )
            session.commit()

        # Build test request
        res = test_client.get("/map_view/test_view")

        assert res.status_code == 200
        response = res.json()
        assert response["map_view_json"] == ""

    def test_get_map_view_unavailable(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        # Build test request
        res = test_client.get("/map_view/test_view")

        assert res.status_code == 404

    @pytest.mark.user("test")
    def test_post_map_view_success(
        self,
        override_get_session,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        minimal_working_example = {
            "map_view_json": {
                "activeBasemapId": "slub-osm",
                "customBasemaps": [],
                "is3dEnabled": False,
                "operationalLayers": [],
                "cameraOptions": {
                    "center": [1039475.3400097956, 6695196.931201956],
                    "bearing": 1.194328566789627,
                    "pitch": 0,
                    "zoom": 11,
                },
            }
        }
        # Build test request
        res = test_client.post("/map_view/", json=minimal_working_example)
        assert res.status_code == 200
        response = res.json()
        assert response["map_view_id"] is not None

    def test_post_map_view_error_invalid_user(
        self, test_client: TestClient, override_get_session_read_only
    ):
        # Build test request
        res = test_client.post("/map_view/", json={"test": 1})

        assert res.status_code == 401

    @pytest.mark.user("test")
    def test_post_map_view_error_invalid_json(
        self,
        test_client: TestClient,
        override_get_session_read_only,
        override_get_user_from_session,
    ):
        res = test_client.post("/map_view/", json={"test": 1})

        assert res.status_code == 422

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from fastapi.testclient import TestClient


class TestStatistics:
    def test_get_statistics(
        self, override_get_session_read_only, test_client: TestClient
    ):
        response = test_client.get("/statistics")
        data = response.json()

        assert response.status_code == 200
        assert len(data["georeference_points"]) == 3
        assert data["georeference_map_count"] == 6
        assert data["not_georeference_map_count"] == 3

    def test_calculate_user_statistics(
        self, override_get_session_read_only, test_client: TestClient
    ):
        response = test_client.get("/statistics")
        data = response.json()

        user_data = data["georeference_points"]

        [user_1_data] = [entry for entry in user_data if entry["user_id"] == "user_1"]

        assert user_1_data is not None

        # 16 georeference processes, 20 points per process
        assert user_1_data["total_points"] == 320
        assert user_1_data["transformation_updates"] == 13
        assert user_1_data["transformation_new"] == 3

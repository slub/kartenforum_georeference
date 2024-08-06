#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import pytest
from fastapi.testclient import TestClient


class TestUserHistory:
    @pytest.mark.user("user_1")
    def test_get_user_history(
        self,
        override_get_session_read_only,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        # Build test request
        res = test_client.get("/user/history")

        assert res.status_code == 200
        assert len(res.json()["georef_profile"]) == 18

    def test_get_user_history_unauthorized(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        # Build test request
        res = test_client.get("/user/history")

        assert res.status_code == 401
        assert res.json() == {"detail": "Not authenticated"}

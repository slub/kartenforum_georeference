#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from fastapi.testclient import TestClient
from sqlmodel import select, Session

from georeference.models.enums import EnumJobState, EnumJobType
from georeference.models.job import Job


class TestJobs:
    def test_get_jobs_success(
        self, override_get_session_read_only, test_client: TestClient
    ):
        response = test_client.get("/jobs")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 13

    def test_get_jobs_success_pending(
        self, override_get_session_read_only, test_client: TestClient
    ):
        response = test_client.get("/jobs?pending=true")
        data = response.json()

        assert response.status_code == 200
        # All jobs are pending in the test db
        assert len(data) == 13

    def test_get_jobs_success_completed_empty(
        self, override_get_session_read_only, test_client: TestClient
    ):
        response = test_client.get("/jobs?pending=false")
        data = response.json()

        assert response.status_code == 200
        # No jobs are completed in the test db
        assert len(data) == 0

    def test_get_jobs_success_completed(
        self,
        db_container,
        override_get_session,
        test_client: TestClient,
    ):
        with Session(db_container[1]) as session:
            job = session.exec(select(Job).limit(1)).one()
            job.state = EnumJobState.COMPLETED.value
            session.add(job)
            session.commit()

        response = test_client.get("/jobs?pending=false")
        data = response.json()

        assert response.status_code == 200
        # All jobs are completed in the test db
        assert len(data) == 1

    def test_get_jobs_success_limit(
        self, override_get_session_read_only, test_client: TestClient
    ):
        response = test_client.get("/jobs?limit=5")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 5

    @pytest.mark.user("user_1")
    def test_post_jobs_success(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/jobs",
            json={
                "name": EnumJobType.TRANSFORMATION_PROCESS.value,
                "description": {"transformation_id": 6990, "comment": "test"},
            },
        )

        assert response.status_code == 200

        assert response.json()["job_id"] == 29

    def test_post_jobs_error_missing_user_id(
        self,
        override_get_session_read_only,
        test_client: TestClient,
    ):
        response = test_client.post(
            "/jobs",
            json={
                "name": "transform_progress",
                "description": {"transformation_id": 123, "comment": "test"},
            },
        )

        # User is missing in the session
        assert response.status_code == 401

    @pytest.mark.user("user_1")
    def test_post_jobs_error_invalid_job_name(
        self,
        override_get_session,
        db_container,
        test_client: TestClient,
        override_get_user_from_session,
    ):
        response = test_client.post(
            "/jobs",
            json={
                "name": "invalid_name",
                "description": {"transformation_id": 123, "comment": "test"},
            },
        )

        # Validation should fail, because the name is not a valid EnumJobType
        assert response.status_code == 422

    @pytest.mark.user("user_1")
    def test_post_jobs_invalid_transformation_id(
        self,
        override_get_session,
        db_container,
        override_get_user_from_session,
        test_client: TestClient,
    ):
        response = test_client.post(
            "/jobs",
            json={
                "name": EnumJobType.TRANSFORMATION_PROCESS.value,
                "description": {"transformation_id": 123, "comment": "test"},
            },
        )

        assert response.status_code == 400

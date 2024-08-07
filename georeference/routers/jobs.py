#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Annotated

# Created by nicolas.looschen@pikobytes.de on 12.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from fastapi import APIRouter, Query, Depends, HTTPException
from loguru import logger
from sqlmodel import select, desc, Session

from georeference.config.constants import GENERAL_ERROR_MESSAGE
from georeference.config.db import get_session
from georeference.models.job import Job
from georeference.models.enums import EnumJobState
from georeference.models.transformation import Transformation
from georeference.schemas.job import JobsResponse, JobResponse
from georeference.schemas.job_payload import JobPayload
from georeference.schemas.user import User
from georeference.utils.auth import require_authenticated_user

router = APIRouter()


def get_filter_state(pending: bool | None):
    if pending is None:
        return None
    elif pending:
        return EnumJobState.NOT_STARTED.value
    else:
        return EnumJobState.COMPLETED.value


@router.get("/", response_model=JobsResponse, tags=["jobs"])
def get_jobs(
    pending: bool | None = Query(None),
    limit: int = Query(100),
    session: Session = Depends(get_session),
):
    try:
        filter_state = get_filter_state(pending)

        statement = select(Job)
        if filter_state:
            statement = statement.where(Job.state == filter_state)
        statement = statement.order_by(desc(Job.submitted)).limit(limit)

        jobs = session.exec(statement).all()

        return [JobResponse.from_sqlmodel(job) for job in jobs]

    except Exception as e:
        logger.warning("Error while trying to return a GET jobs request.")
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


@router.post("/", tags=["jobs"])
def post_job(
    new_job: JobPayload,
    user: Annotated[User, Depends(require_authenticated_user)],
    session: Session = Depends(get_session),
):
    logger.debug("Start validating transformation for new job.")
    transformation_id = new_job.description.transformation_id

    logger.debug(f"Transformation ID: {transformation_id}")
    transformation = session.exec(
        select(Transformation).where(Transformation.id == transformation_id)
    ).first()

    if transformation is None:
        logger.warning(f"Transformation with id {transformation_id} does not exist.")
        raise HTTPException(
            detail="Referenced transformation does not exist.", status_code=400
        )

    try:
        logger.debug("Transformation is valid.")
        logger.debug("Add the job to the database.")

        job = Job.from_payload(new_job, user.username)
        session.add(job)
        session.commit()

        logger.debug(f"Job with id {job.id} was added to the database.")
        return {"job_id": job.id}
    except Exception as e:
        logger.info("Error while trying to return a POST jobs request.")
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)

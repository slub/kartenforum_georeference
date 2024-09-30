#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 25.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session
import json
from datetime import datetime
from typing import Annotated

from georeference.config.constants import GENERAL_ERROR_MESSAGE
from georeference.config.db import get_session
from georeference.config.settings import get_settings
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job
from georeference.models.mosaic_map import MosaicMap
from georeference.schemas.mosaic_map import (
    MosaicMapsResponse,
    MosaicMapResponse,
    MosaicMapPayload,
)
from georeference.schemas.user import User
from georeference.utils.auth import require_user_role
from georeference.utils.parser import from_public_map_id

router = APIRouter(tags=["mosaic_maps"])
settings = get_settings()


@router.get("/", response_model=MosaicMapsResponse)
def get_mosaic_maps(session: Annotated[Session, Depends(get_session)]):
    try:
        response_objs = []
        for mosaic_map in MosaicMap.all(session):
            response_objs.append(MosaicMapResponse.from_model(mosaic_map))
        return response_objs

    except Exception as e:
        logger.warning("Error while trying to return a GET mosaic_maps request.")
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


@router.get("/{public_mosaic_map_id}", response_model=MosaicMapResponse)
def get_mosaic_map(
    public_mosaic_map_id: str, session: Annotated[Session, Depends(get_session)]
):
    try:
        mosaic_map = MosaicMap.by_public_id(public_mosaic_map_id, session)
        if mosaic_map is None:
            logger.warning(f"Mosaic map with id {public_mosaic_map_id} not found.")
            raise HTTPException(status_code=404, detail="Mosaic map not found")

        return MosaicMapResponse.from_model(mosaic_map)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            f"Error while trying to return a GET mosaic_map request for id {public_mosaic_map_id}."
        )
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


@router.delete("/{public_mosaic_map_id}")
def delete_mosaic_map(
    public_mosaic_map_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(require_user_role(settings.ADMIN_ROLE))],
):
    try:
        mosaic_map = MosaicMap.by_public_id(public_mosaic_map_id, session)
        if mosaic_map is None:
            logger.warning(f"Mosaic map with id {public_mosaic_map_id} not found.")
            raise HTTPException(status_code=404, detail="Mosaic map not found")

        _add_job(
            session,
            mosaic_map.id,
            mosaic_map.name,
            user_id=user.username,
            is_delete=True,
        )

        session.delete(mosaic_map)
        session.commit()

        return {
            "mosaic_map_id": public_mosaic_map_id,
            "message": "Mosaic map scheduled for deletion.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            f"Error while trying to delete a mosaic_map with id {public_mosaic_map_id}."
        )
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


@router.post("/", response_model=MosaicMapResponse)
def create_mosaic_map(
    new_mosaic_map: MosaicMapPayload,
    user: Annotated[User, Depends(require_user_role(settings.ADMIN_ROLE))],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        mosaic_map_data = {
            **new_mosaic_map.model_dump(),
            "raw_map_ids": list(
                map(lambda x: from_public_map_id(x), new_mosaic_map.raw_map_ids)
            ),
            "last_change": datetime.now(),
        }

        mosaic_map = MosaicMap(**mosaic_map_data)

        session.add(mosaic_map)
        session.commit()

        _add_job(
            session,
            mosaic_map.id,
            mosaic_map.name,
            user_id=user.username,
            is_delete=False,
        )

        return MosaicMapResponse.from_model(mosaic_map)

    except Exception as e:
        logger.warning("Error while trying to post a mosaic_map.")
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


@router.post("/{public_mosaic_map_id}")
def update_mosaic_map(
    mosaic_map_update: MosaicMapPayload,
    public_mosaic_map_id: str,
    user: Annotated[User, Depends(require_user_role(settings.ADMIN_ROLE))],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        mosaic_map = MosaicMap.by_public_id(public_mosaic_map_id, session)
        if mosaic_map is None:
            raise HTTPException(status_code=404, detail="Mosaic map not found")

        # Update the values
        mosaic_map.raw_map_ids = list(
            map(lambda x: from_public_map_id(x), mosaic_map_update.raw_map_ids)
        )
        mosaic_map.name = mosaic_map_update.name
        mosaic_map.title = mosaic_map_update.title
        mosaic_map.title_short = mosaic_map_update.title_short
        mosaic_map.description = mosaic_map_update.description
        mosaic_map.time_of_publication = mosaic_map_update.time_of_publication
        mosaic_map.link_thumb = mosaic_map_update.link_thumb
        mosaic_map.map_scale = mosaic_map_update.map_scale
        mosaic_map.last_change = datetime.now()

        session.commit()

        _add_job(
            session,
            mosaic_map.id,
            mosaic_map.name,
            user_id=user.username,
            is_delete=False,
        )

        return MosaicMapResponse.from_model(mosaic_map)

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            f"Error while trying to update a mosaic_map with id {mosaic_map_update.id}."
        )
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


@router.post("/{public_mosaic_map_id}/refresh")
def refresh_mosaic_map(
    public_mosaic_map_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: User = Depends(require_user_role(settings.ADMIN_ROLE)),
):
    try:
        mosaic_map = MosaicMap.by_public_id(public_mosaic_map_id, session)
        if mosaic_map is None:
            logger.warning(f"Mosaic map with id {public_mosaic_map_id} not found.")
            raise HTTPException(status_code=404, detail="Mosaic map not found")

        _add_job(
            session, mosaic_map.id, mosaic_map.name, user.username, is_delete=False
        )

        return {
            "mosaic_map_id": public_mosaic_map_id,
            "message": "Mosaic map scheduled for refresh.",
        }

    except Exception as e:
        logger.warning(
            f"Error while trying to refresh a mosaic_map with id {public_mosaic_map_id}."
        )
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


def _add_job(
    session: Session, mosaic_map_id, mosaic_map_name, user_id="system", is_delete=False
):
    """
    Handles the job creation for adding/updating maps, based on the supplied values

    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param mosaic_map_id: Id of the mosaic_map
    :type mosaic_map_id: int
    :param mosaic_map_name: Name of the mosaic_map
    :type mosaic_map_name: str
    :param user_id: id of the user
    :type user_id: str
    :param is_delete: Flag if an existing map was updated or a new map was created
    :type is_delete: bool
    """
    create_job = Job(
        description=json.dumps(
            {"mosaic_map_id": mosaic_map_id, "mosaic_map_name": mosaic_map_name},
            ensure_ascii=False,
        ),
        type=EnumJobType.MOSAIC_MAP_DELETE.value
        if is_delete
        else EnumJobType.MOSAIC_MAP_CREATE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now(),
        user_id=user_id,
    )

    session.add(create_job)
    session.commit()

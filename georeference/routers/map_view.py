#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from typing import Union, Annotated

# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session

from georeference.config.db import get_session
from georeference.models.map_view import MapView
from georeference.schemas.map_view import (
    MapViewResponse,
    TwoDimensionalMapViewJson,
    ThreeDimensionalMapViewJson,
)
from georeference.schemas.user import User
from georeference.utils.auth import require_authenticated_user

router = APIRouter()


@router.get("/{public_map_view_id}", response_model=MapViewResponse, tags=["map_view"])
def get_map_view(public_map_view_id: str, session: Session = Depends(get_session)):
    logger.debug(f"Start fetching map view with public_id: {public_map_view_id}")
    map_view = MapView.by_public_id(public_map_view_id, session)
    if map_view is None:
        logger.warning(f"Map view with id {public_map_view_id} not found.")
        raise HTTPException(status_code=404, detail="Map view not found")

    logger.debug(
        f"Updating last access for map view with public_id: {public_map_view_id}"
    )
    map_view.update_last_access(session)

    logger.debug(f"Returning map view with public_id: {public_map_view_id}")

    # @TODO: This should probably be the map_view_json directly and it should be validated before being returned
    return MapViewResponse(map_view_json=map_view.map_view_json)


@router.post("/", tags=["map_view"])
def post_map_view(
    new_map_view: Union[TwoDimensionalMapViewJson, ThreeDimensionalMapViewJson],
    user: Annotated[User, Depends(require_authenticated_user)],
    session: Session = Depends(get_session),
):
    user_id = user.username
    submitted = datetime.now()
    public_id = str(uuid.uuid4())

    # if the id is not unique, regenerate public_id
    while MapView.by_public_id(public_id, session) is not None:
        public_id = str(uuid.uuid4())

    new_map_view = MapView(
        map_view_json=new_map_view.model_dump_json(),
        last_request=None,
        request_count=0,
        submitted=submitted,
        user_id=user_id,
        public_id=public_id,
    )
    session.add(new_map_view)
    session.commit()

    return {"map_view_id": new_map_view.public_id}

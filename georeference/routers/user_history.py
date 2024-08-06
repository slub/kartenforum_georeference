#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
# Created by nicolas.looschen@pikobytes.de on 10.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc, col
from loguru import logger

from georeference.config.constants import GENERAL_ERROR_MESSAGE
from georeference.config.db import get_session
from georeference.models.georef_map import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation, EnumValidationValue
from georeference.schemas.user import User
from georeference.utils.auth import require_authenticated_user
from georeference.utils.parser import to_public_map_id

router = APIRouter(tags=["history"])


@router.get("/")
async def get_user_history(
    user: Annotated[User, Depends(require_authenticated_user)],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        logger.debug(
            "Query georeference profile information from database for user {}",
            user.username,
        )
        statement = (
            select(Transformation, Metadata, RawMap, GeorefMap)
            .join(
                Metadata,
                col(Transformation.raw_map_id) == col(Metadata.raw_map_id),
                isouter=True,
            )
            .join(RawMap)
            .join(GeorefMap, isouter=True)
            .where(Transformation.user_id == user.username)
            .order_by(desc(Transformation.id))
        )

        logger.debug("Create response list")

        data = session.exec(statement).all()
        georef_profile = []
        points = 0
        for record in data:
            transformation_obj = record[0]
            metadata_obj = record[1]
            map_obj = record[2]
            georef_map_obj = record[3]

            # Create response
            response_record = {
                "file_name": map_obj.file_name,
                "is_transformed": True if georef_map_obj is not None else False,
                "map_id": to_public_map_id(map_obj.id),
                "transformation": {
                    "id": transformation_obj.id,
                    "params": transformation_obj.get_params_as_dict(),
                    "submitted": str(transformation_obj.submitted),
                    "validation": transformation_obj.validation,
                },
                "metadata": {
                    "thumbnail": metadata_obj.link_thumb_mid,
                    "time_published": str(metadata_obj.time_of_publication),
                    "title": metadata_obj.title,
                },
            }

            # calculate points
            if transformation_obj.validation != EnumValidationValue.INVALID.value:
                points += 20

            georef_profile.append(response_record)

        logger.debug("Response: {}", georef_profile)

        return {"georef_profile": georef_profile, "points": points}

    except Exception as e:
        logger.error(
            "Error while trying to request georeference history information: {}",
            e,
        )
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=GENERAL_ERROR_MESSAGE)

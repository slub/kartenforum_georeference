#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from sqlalchemy import func, case
from sqlmodel import select, and_, Session, col

from georeference.config.constants import GENERAL_ERROR_MESSAGE
from georeference.config.db import get_session
from georeference.models.georef_map import GeorefMap
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation, EnumValidationValue

router = APIRouter()


@router.get("/", tags=["statistics"])
def get_statistics(session: Session = Depends(get_session)):
    try:
        logger.info("Request - Get georeference points.")
        statement = (
            select(
                Transformation.user_id,
                # count total number of georeference processes for each user
                func.sum(
                    case(
                        (
                            Transformation.validation
                            != EnumValidationValue.INVALID.value,
                            1,
                        ),
                        else_=0,
                    )
                ).label("occurrence"),
                # count number of valid transformations for each user of type "new" (no overwrites)
                func.sum(
                    case(
                        (
                            and_(
                                Transformation.validation
                                != EnumValidationValue.INVALID.value,
                                Transformation.overwrites == 0,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                # count number of valid transformations for each user of type "update" (overwrites)
                func.sum(
                    case(
                        (
                            and_(
                                Transformation.validation
                                != EnumValidationValue.INVALID.value,
                                Transformation.overwrites > 0,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
            )
            .group_by(Transformation.user_id)
            .order_by("occurrence")
            .limit(20)
        )

        data = session.exec(statement).all()

        # Create ranking list
        user_points = []
        for record in data:
            userid = record[0]
            points = record[1] * 20
            new = record[2] if record[2] is not None else 0
            update = record[3] if record[3] is not None else 0
            user_points.append(
                {
                    "user_id": userid,
                    "total_points": points,
                    "transformation_new": new,
                    "transformation_updates": update,
                }
            )

        logger.debug("Get georeference and missing georeference map count")

        statement = select(
            func.count(RawMap.id),
            func.sum(case((col(GeorefMap.raw_map_id).is_(None), 1), else_=0)),
        ).join(GeorefMap, isouter=True)

        total_count_data = session.exec(statement).first()

        georeference_map_count = total_count_data[0] - total_count_data[1]
        missing_georeference_map_count = total_count_data[1]

        return {
            "georeference_points": user_points,
            "georeference_map_count": georeference_map_count,
            "not_georeference_map_count": missing_georeference_map_count,
        }
    except Exception as e:
        logger.error("Error while trying to get statistics: {}", e)
        logger.error(traceback.format_exc())

        raise HTTPException(status_code=500, detail=GENERAL_ERROR_MESSAGE)

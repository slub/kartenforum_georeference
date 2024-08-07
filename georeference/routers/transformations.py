#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import uuid
from datetime import datetime
from typing import Annotated

# Created by nicolas.looschen@pikobytes.de on 26.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from fastapi import APIRouter, Depends, Query, HTTPException
from loguru import logger
from sqlmodel import Session, select, desc

from georeference.config.constants import GENERAL_ERROR_MESSAGE
from georeference.config.db import get_session
from georeference.config.settings import get_settings
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.georef_map import GeorefMap
from georeference.models.job import Job
from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation, EnumValidationValue
from georeference.schemas.transformation import (
    TransformationResponse,
    TransformationResponseAdditionalProperties,
    TransformationsResponse,
    TransformationPayload,
)
from georeference.schemas.user import User
from georeference.utils.auth import require_authenticated_user
from georeference.utils.georeference import get_image_extent
from georeference.utils.parser import from_public_map_id, to_public_map_id, to_int
from georeference.utils.proj import (
    transform_to_params_to_target_crs,
    get_crs_for_transformation_params,
)
from georeference.utils.temp_files import (
    _create_temporary_georeference_image,
    _create_temporary_mapfile,
)

router = APIRouter()
settings = get_settings()


@router.get(
    "/",
    response_model=TransformationsResponse,
    tags=["transformations"],
    response_model_exclude_none=True,
)
def get_transformations(
    session: Annotated[Session, Depends(get_session)],
    user_id: str | None = Query(None),
    map_id: str | None = Query(None),
    validation: EnumValidationValue | None = Query(None),
    additional_properties: bool = Query(False),
    user: User = Depends(require_authenticated_user),
):
    try:
        statement = (
            select(Transformation, RawMap, Metadata, GeorefMap)
            .join(RawMap, Transformation.raw_map_id == RawMap.id)
            .join(Metadata, Transformation.raw_map_id == Metadata.raw_map_id)
            .join(
                GeorefMap,
                Transformation.id == GeorefMap.transformation_id,
                isouter=True,
            )
        )

        if user_id is not None:
            statement = statement.where(Transformation.user_id == user_id)
        if map_id is not None:
            statement = statement.where(
                Transformation.raw_map_id == from_public_map_id(map_id)
            )
        if validation is not None:
            statement = statement.where(Transformation.validation == validation.value)

        statement = statement.order_by(desc(Transformation.submitted))
        transformations = session.exec(statement).all()

        responses = []
        for transformation in transformations:
            transformation_obj = transformation[0]
            map_ob = transformation[1]
            metadata_obj = transformation[2]
            georef_map_obj = transformation[3]

            responses.append(
                _to_transformation_response(
                    transformation_obj,
                    metadata_obj,
                    to_public_map_id(map_ob.id),
                    session,
                    georef_map_obj is not None,
                )
            )

        response_additional_properties = None

        if additional_properties and len(transformations) > 0:
            response_additional_properties = _create_additional_properties(
                transformations[0][1], session
            )

        return TransformationsResponse(
            transformations=responses,
            additional_properties=response_additional_properties,
        )

    except Exception as e:
        logger.warning("Error while trying to return a GET transformations request.")
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


@router.post("/", response_model=None, tags=["transformations"])
def create_transformation(
    transformation: TransformationPayload,
    user: Annotated[User, Depends(require_authenticated_user)],
    dry_run: bool = Query(False),
    session: Session = Depends(get_session),
):
    try:
        transformation_id = (
            transformation.transformation_id
            if hasattr(transformation, "transformation_id")
            else None
        )

        transformation_obj = None
        if transformation_id is not None:
            transformation_obj = Transformation.by_id(transformation_id, session)

        map_obj_id = (
            transformation_obj.raw_map_id
            if transformation_obj is not None
            else to_int(from_public_map_id((transformation.map_id)))
        )

        map_obj = RawMap.by_id(map_obj_id, session)

        if map_obj is None:
            logger.warning(f"Map with id {transformation.map_id} not found.")
            raise HTTPException(
                detail="Referenced map does not exist.", status_code=400
            )

        if transformation_obj is not None:
            if dry_run:
                return _handle_transformation_dry_run(
                    map_obj,
                    transformation_obj.get_params_as_dict(),
                    transformation_obj.get_target_crs_as_string(),
                    # On dry_runs we never use clip, because we want to allow the user in the client to draw
                    # clip polygons based on the full georeference image.
                    clip=None,
                )
            else:
                raise HTTPException(
                    detail="Requests with transformation_id are only allowed with the dry_run flag.",
                    status_code=400,
                )
        else:
            return _handle_request_with_transformation_payload(
                transformation, map_obj, dry_run, user.username, session
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Error while trying to return a POST transformations request.")
        logger.error(e)
        raise HTTPException(detail=GENERAL_ERROR_MESSAGE, status_code=500)


def _to_transformation_response(
    transformation_obj, metadata_obj, map_id, dbsession, is_active=False
):
    clip_geojson = (
        Transformation.get_valid_clip_geometry(
            transformation_obj.id, dbsession=dbsession
        )
        if transformation_obj.clip is not None
        else None
    )

    if clip_geojson is not None and "crs" not in clip_geojson:
        clip_geojson["crs"] = {"type": "name", "properties": {"name": "EPSG:4326"}}

    data = {
        **transformation_obj.model_dump(),
        "transformation_id": transformation_obj.id,
        "clip": clip_geojson,
        "is_active": is_active,
        "map_id": map_id,
        "metadata": metadata_obj.model_dump(),
        "params": transformation_obj.get_params_as_dict_in_epsg_4326(),
    }

    return TransformationResponse(**data)


def _create_additional_properties(raw_map_obj, dbsession):
    georef_map_obj = GeorefMap.by_raw_map_id(raw_map_obj.id, dbsession)
    metadata_obj = Metadata.by_map_id(raw_map_obj.id, dbsession)

    data = {
        "active_transformation_id": georef_map_obj.transformation_id
        if georef_map_obj is not None
        else None,
        "default_crs": f"EPSG:{raw_map_obj.default_crs}",
        "extent": json.loads(georef_map_obj.extent)
        if georef_map_obj is not None and georef_map_obj.extent is not None
        else None,
        "metadata": metadata_obj.model_dump(),
        "pending_jobs": Job.has_not_started_jobs_for_map_id(dbsession, raw_map_obj.id),
    }

    return TransformationResponseAdditionalProperties(**data)


def _handle_transformation_dry_run(
    map_obj, transformation_params, target_crs, clip=None
):
    """Handles the dry_run for POST transformation requests.

    :param map_obj: RawMap
    :type map_obj: georeference.models.raw_maps.RawMap
    :param transformation_params: Dict describing the transformation_params
    :type transformation_params: Dict
    :param target_crs: ESPG code of the target crs
    :type target_crs: str
    :param clip: Clip geometry
    :type clip: dict
    :result: JSON object describing the map object
    :rtype: {{
        "extent": [number, number, number, number],
        "layer_name": str,
        "wms_url": str,
    }}
    """
    correct_transformation_params = transform_to_params_to_target_crs(
        transformation_params, target_crs
    )

    # Create temporary georeference file
    trg_file_name = "{}::{}.tif".format(map_obj.file_name, uuid.uuid4())
    trg_file = _create_temporary_georeference_image(
        trg_file_name, map_obj.get_abs_path(), correct_transformation_params, clip
    )

    # Create temporary mapfile
    wms_url = _create_temporary_mapfile(
        map_obj, trg_file_name, correct_transformation_params
    )

    return {
        "extent": get_image_extent(trg_file),
        "layer_name": map_obj.file_name,
        "wms_url": wms_url,
    }


# @TODO: Remove request api
def _handle_request_with_transformation_payload(
    payload: TransformationPayload, map_obj, dry_run, user_id, session
):
    """Handles a request which supplies a transformation object in its json body.

    :param request: Request object
    :type request: pyramid.Request
    :param map_obj: RawMap
    :type map_obj: georeference.models.raw_maps.RawMap
    :param dry_run: Flag indicating whether the changes should be written to the db.
    :type dry_run: bool
    """
    clip = None if payload.clip is None else payload.clip.model_dump()
    transformation_params = payload.params.model_dump()

    # inject legacy settings - static values, but required by the job runners
    transformation_params["target"] = "EPSG:4326"
    transformation_params["source"] = "pixel"

    if clip is not None:
        clip["crs"] = {"type": "name", "properties": {"name": "EPSG:4326"}}

    if dry_run:
        # Parse correct transformation data
        target_crs = get_crs_for_transformation_params(
            transformation_params, map_obj, target_crs=None
        )

        return _handle_transformation_dry_run(
            map_obj, transformation_params, target_crs, clip=None
        )
    else:
        return _handle_transformation_write(
            map_obj,
            payload,
            clip=clip,
            transformation_params=transformation_params,
            user_id=user_id,
            dbsession=session,
        )


def _handle_transformation_write(
    raw_map_obj,
    payload: TransformationPayload,
    clip,
    transformation_params,
    user_id,
    dbsession,
):
    """Handles the permanent POST for transformation requests.

    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param json_body: Json object containing the transformation parameters
    :type json_body: TransformationSchema
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: JSON object describing the map object
    :rtype: {{
        "transformation_id": number,
        "job_id": number,
        "points" : number,
    }}
    """
    # Parse all relevant transformations params
    target_crs = get_crs_for_transformation_params(
        transformation_params, raw_map_obj, target_crs=None
    )
    overwrites = payload.overwrites
    user_id = user_id
    submitted = datetime.now()

    # If overwrites == 0, we check if there is already a valid transformation registered for the original map id.
    has_transformation = Transformation.has_transformation(raw_map_obj.id, dbsession)

    if overwrites == 0 and has_transformation:
        logger.warning(f"Transformation already exists for map with id {raw_map_obj.id}.")

        raise HTTPException(
            detail="It is forbidden to register a new transformation for an original map, which already has a transformation registered.",
            status_code=400,
        )

    # Save to transformations
    new_transformation = Transformation(
        submitted=submitted,
        user_id=user_id,
        params=json.dumps(transformation_params),
        target_crs=int(target_crs.split(":")[1]),
        clip=json.dumps(clip) if clip is not None else None,
        validation=EnumValidationValue.MISSING.value,
        raw_map_id=raw_map_obj.id,
        overwrites=overwrites,
        comment=None,
    )
    dbsession.add(new_transformation)
    dbsession.flush()

    # Save to jobs
    new_job = Job(
        description=json.dumps({"transformation_id": new_transformation.id}),
        type=EnumJobType.TRANSFORMATION_PROCESS.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=submitted,
        user_id=user_id,
        comment=None,
    )
    dbsession.add(new_job)
    dbsession.commit()

    return {
        "transformation_id": new_transformation.id,
        "job_id": new_job.id,
        "points": int(len(transformation_params["gcps"])) * 5,
    }

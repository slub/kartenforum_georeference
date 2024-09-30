#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 24.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os
import uuid
from datetime import datetime

import sqlalchemy.exc
import streaming_form_data
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from osgeo import gdal
from sqlalchemy import text
from sqlmodel import Session, select
from starlette import status
from starlette.requests import Request, ClientDisconnect
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, ValueTarget
from streaming_form_data.validators import MaxSizeValidator

from georeference.config.constants import GENERAL_ERROR_MESSAGE
from georeference.config.db import get_session
from georeference.config.paths import PATH_TMP_NEW_MAP_ROOT
from georeference.config.settings import get_settings
from georeference.models.enums import EnumJobState, EnumJobType
from georeference.models.georef_map import GeorefMap
from georeference.models.job import Job
from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.schemas.map import MapResponse, MetadataPayload
from georeference.schemas.user import User
from georeference.utils.auth import require_user_role
from georeference.utils.max_body_size_validator import (
    MAX_REQUEST_BODY_SIZE,
    MaxBodySizeValidator,
    MaxBodySizeException,
    MAX_FILE_SIZE,
)
from georeference.utils.parser import to_public_map_id, parse_public_map_id

router = APIRouter()
settings = get_settings()


# @TODO: This was previously not exposed to the public
@router.get("/{map_id}", response_model=MapResponse, tags=["maps"])
def get_map_for_mapid(map_id: str, session: Session = Depends(get_session)):
    try:
        logger.debug(f"Start fetching map with public map_id: {map_id}")
        parsed_map_id = parse_public_map_id(map_id)
        logger.debug(f"Parsed map id {parsed_map_id} from public map id {map_id}")

        logger.debug(f"Load RawMap, Metadata and GeorefMap for map_id: {parsed_map_id}")
        statement = (
            select(RawMap, Metadata, GeorefMap)
            .join(Metadata, isouter=True)
            .join(GeorefMap, isouter=True)
            .where(RawMap.id == parsed_map_id)
        )

        try:
            raw_map_obj, metadata_obj, georef_map_obj = session.exec(statement).one()
        except sqlalchemy.exc.NoResultFound:
            logger.warning(f"Map with id {parsed_map_id} not found.")
            raise HTTPException(status_code=404, detail="Map not found")
        except sqlalchemy.exc.MultipleResultsFound:
            # This case should not be possible, but still catch it
            logger.warning(f"Multiple results found for map with id {parsed_map_id}.")
            raise HTTPException(status_code=500, detail=GENERAL_ERROR_MESSAGE)

        logger.debug(f"Create MapResponse object for map_id: {parsed_map_id}")
        input_dict = {
            **raw_map_obj.model_dump(),
            **metadata_obj.model_dump(),
            "map_id": map_id,
            "transformation_id": georef_map_obj.transformation_id
            if georef_map_obj
            else None,
        }

        return MapResponse(**input_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.info("Error while trying to return a GET map request.")
        logger.error(e)
        raise HTTPException(status_code=500, detail=GENERAL_ERROR_MESSAGE)


@router.delete("/{map_id}", tags=["maps"])
def delete_map_for_mapid(
    map_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user_role(settings.ADMIN_ROLE)),
):
    try:
        logger.debug(f"Start deleting map with public map_id: {map_id}")
        parsed_map_id = parse_public_map_id(map_id)
        logger.debug(f"Parsed map id {parsed_map_id} from public map id {map_id}")

        user_id = user.username
        logger.debug(f"User {user_id} is trying to delete map with id {parsed_map_id}")

        logger.debug(f"Check if map with id {parsed_map_id} exists")
        if not _exists_map_id(session, parsed_map_id):
            logger.warning(f"Map with id {parsed_map_id} not found.")
            raise HTTPException(status_code=404, detail="Map not found")

        delete_job = Job(
            description=json.dumps({"map_id": parsed_map_id}),
            type=EnumJobType.MAPS_DELETE.value,
            submitted=datetime.now(),
            state=EnumJobState.NOT_STARTED.value,
            user_id=user_id,
        )

        session.add(delete_job)
        session.commit()

        return {"message": "Scheduled deletion for map.", "map_id": map_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.info("Error while trying to handle a DELETE map request.")
        logger.error(e)
        raise HTTPException(status_code=500, detail=GENERAL_ERROR_MESSAGE)


@router.post("/{map_id}", tags=["maps"])
async def post_update_map(
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(require_user_role(settings.ADMIN_ROLE)),
    map_id: str = None,
):
    try:
        file_, data, filepath = await register_streaming_form_data(request)

        parsed_map_id = parse_public_map_id(map_id)
        exists_map, raw_map = _exists_map_id(session, parsed_map_id)
        if not exists_map:
            logger.warning(f"Map with id {map_id} not found.")
            raise HTTPException(status_code=404, detail="Map not found")

        metadata_update = None
        metadata = data.value.decode()
        exists_file = file_.multipart_filename is not None
        exists_metadata = metadata is not None and metadata != ""

        if not exists_file and not exists_metadata:
            logger.warning("No metadata or file was provided.")
            raise HTTPException(
                status_code=400, detail="No metadata or file was provided."
            )

        if exists_metadata:
            try:
                metadata = json.loads(metadata)
                MetadataPayload.model_validate(metadata)
            except ValueError:
                logger.warning("Invalid metadata provided.")
                raise HTTPException(
                    status_code=400, detail="Invalid metadata provided."
                )

            metadata_obj = Metadata.by_map_id(parsed_map_id, session)
            metadata_update = {
                **metadata_obj.model_dump(),
                **_get_defined_keys(
                    raw_map.model_dump(), ["map_type", "default_crs", "map_scale"]
                ),
                **metadata,
                "time_of_publication": metadata["time_of_publication"]
                if "time_of_publication" in metadata
                else metadata_obj.time_of_publication.isoformat(),
            }

        if exists_file:
            try:
                _validate_file(filepath)
            except Exception as e:
                os.remove(filepath)
                raise e

        _add_job(
            session,
            metadata_update,
            filepath if file_.multipart_filename is not None else None,
            file_.multipart_filename,
            raw_map.id,
            user.username,
            is_update=True,
        )
        return {"message": "Scheduled update for map.", "map_id": map_id}
    except ClientDisconnect:
        logger.warning("Client disconnected while trying to update map.")
    except MaxBodySizeException as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Maximum request body size limit ({MAX_REQUEST_BODY_SIZE} bytes) exceeded ({e.body_len} bytes read)",
        )
    except streaming_form_data.validators.ValidationError:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Maximum file size limit ({MAX_FILE_SIZE} bytes) exceeded",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error while trying to update map with id {map_id}")
        logger.error(e)
        raise HTTPException(status_code=500, detail=GENERAL_ERROR_MESSAGE)


@router.post("/", tags=["maps"])
async def post_create_map(
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(require_user_role(settings.ADMIN_ROLE)),
):
    try:
        file_, data, filepath = await register_streaming_form_data(request)

        metadata = data.value.decode()
        if metadata is None or metadata == "":
            logger.warning("No metadata was provided on map create.")
            raise HTTPException(
                status_code=400, detail="The metadata form field is required."
            )

        if not file_.multipart_filename:
            logger.warning("No file was provided on map create.")
            raise HTTPException(
                status_code=400, detail="The file form field is required."
            )

        try:
            metadata = json.loads(metadata)
            MetadataPayload.model_validate(metadata)
        except ValueError:
            logger.warning("Invalid metadata provided.")
            raise HTTPException(status_code=400, detail="Invalid metadata provided.")

        try:
            _validate_file(filepath)
        except Exception as e:
            os.remove(filepath)
            raise e

        # Get map id from sequence
        (map_id,), *rest = session.execute(
            text("SELECT nextval('public.raw_maps_id_seq') AS map_id")
        )

        _add_job(
            session,
            metadata,
            filepath,
            file_.multipart_filename,
            map_id,
            user.username,
            is_update=False,
        )

        return {
            "message": "Scheduled creation process for map.",
            "map_id": to_public_map_id(map_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Error while trying to create map.")
        logger.error(e)
        raise HTTPException(status_code=500, detail=GENERAL_ERROR_MESSAGE)


def _exists_map_id(session: Session, map_id: int):
    try:
        raw_map = session.exec(select(RawMap).where(RawMap.id == map_id)).one()
        if raw_map:
            return True, raw_map
    except sqlalchemy.exc.NoResultFound:
        return False, None


def _add_job(
    session,
    metadata,
    file_path,
    upload_file_name,
    map_id,
    user_id="system",
    is_update=False,
):
    """
    Handles the job creation for adding/updating maps, based on the supplied values

    :param: request - pyramid request object
    :param: metadata - uploaded metadata as json object
    :param: file_path - path to the file in the directory system
    :param: upload_file_name - original name the file was uploaded with
    :param: map_id - id of the map
    :param: user_id - id of the user
    :param: is_update - flag if an existing map was updated or a new map was created
    """
    create_job = Job(
        description=json.dumps(
            {
                "map_id": map_id,
                "metadata": metadata,
                "file": file_path,
                "original_file_name": upload_file_name,
            },
            ensure_ascii=False,
        ),
        type=EnumJobType.MAPS_UPDATE.value
        if is_update
        else EnumJobType.MAPS_CREATE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now(),
        user_id=user_id,
    )

    session.add(create_job)
    session.commit()


def generate_tmp_file_name():
    unique_id = str(uuid.uuid4())

    return os.path.join(PATH_TMP_NEW_MAP_ROOT, f"{unique_id}.tif")


async def register_streaming_form_data(request: Request):
    body_validator = MaxBodySizeValidator(MAX_REQUEST_BODY_SIZE)

    filepath = generate_tmp_file_name()
    file_ = FileTarget(filepath, validator=MaxSizeValidator(MAX_FILE_SIZE))
    data = ValueTarget()
    parser = StreamingFormDataParser(headers=request.headers)
    parser.register("file", file_)
    parser.register("metadata", data)

    async for chunk in request.stream():
        body_validator(chunk)
        parser.data_received(chunk)

    return file_, data, filepath


def _validate_file(path_to_file):
    """
    Check if the file is really a geotiff file.
    :param path_to_file: file path
    :type path_to_file: str
    """
    try:
        gtif = gdal.Open(path_to_file)
        driver_name = None if gtif is None else gtif.GetDriver().ShortName
        if driver_name != "GTiff":
            logger.warning("Invalid file format.")
            raise RuntimeError()
    except RuntimeError:
        err_message = "Invalid file object at POST request."
        logger.warning(err_message)
        raise HTTPException(status_code=400, detail=err_message)


def _get_defined_keys(obj, keys):
    result = {}
    for key in keys:
        if key in obj and obj[key] is not None:
            result[key] = obj[key]
    return result

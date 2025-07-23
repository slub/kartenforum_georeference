#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 29.04.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

from datetime import datetime
import uuid
from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, HTTPException, Response, status
from geojson_pydantic import FeatureCollection
from httpx import AsyncClient
import httpx
from pydantic import ValidationError
from sqlmodel import Session

from georeference.config import settings
from georeference.config.db import get_session
from georeference.models.vector_map_external import (
    VectorMapExternal,
)

from georeference.routers.vector_map import push_vector_map_to_index
from georeference.schemas.vector_map_external import (
    VectorMapExternalIdResponse,
    VectorMapExternalPayload,
    VectorMapExternalCreate,
    VectorMapExternalResponse,
)
from georeference.utils.auth import require_user_role

from georeference.utils.es_index.es_index_async import get_async_es_client
from georeference.utils.http_client import get_http_client


router = APIRouter()
app_settings = settings.get_settings()


def get_vector_map(public_id: uuid.UUID, session: Session):
    vector_map = VectorMapExternal.by_public_id(public_id, session)

    if vector_map is None:
        raise HTTPException(status_code=404, detail="Vector map not found")

    return vector_map


async def fetch_and_validate_geojson(url: str, http_client: AsyncClient):
    try:
        response = await http_client.get(url)
        response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=422, detail="Cannot get response from content url"
        )

    try:
        geojson = FeatureCollection.model_validate(response.json())
    except ValidationError:
        raise HTTPException(
            status_code=422, detail="Geojson from content url is not valid"
        )

    return geojson


@router.get(
    "/{vector_map_id}",
    tags=["vector_map_external"],
    response_model=VectorMapExternalResponse,
    dependencies=[Depends(require_user_role(app_settings.ADMIN_ROLE))],
)
def read_external_vector_map(
    vector_map_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    response = VectorMapExternalResponse(
        id=vector_map.public_id,
        title=vector_map.title,
        description=vector_map.description,
        link_thumb=vector_map.link_thumb,
        link_content=vector_map.link_content,
        content_type=vector_map.content_type,
        time_period=vector_map.time_period,
        submitted=vector_map.submitted,
        last_change=vector_map.last_change,
    )

    # Update telemetry
    vector_map.request_count += 1
    vector_map.last_request = datetime.now()
    session.add(vector_map)
    session.commit()

    return response


@router.post(
    "/",
    status_code=201,
    tags=["vector_map_external"],
    response_model=VectorMapExternalIdResponse,
    dependencies=[Depends(require_user_role(app_settings.ADMIN_ROLE))],
)
async def create_new_external_vector_map(
    new_vector_map: VectorMapExternalCreate,
    session: Session = Depends(get_session),
    http_client: AsyncClient = Depends(get_http_client),
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
):
    vector_map = new_vector_map.to_db_model()

    geojson = await fetch_and_validate_geojson(vector_map.link_content, http_client)

    session.add(vector_map)
    session.commit()
    session.refresh(vector_map)

    await push_vector_map_to_index(
        vector_map, geojson.model_dump_json(exclude_unset=True), es_index
    )

    return {"id": vector_map.public_id}


@router.put(
    "/{vector_map_id}",
    tags=["vector_map_external"],
    response_model=VectorMapExternalResponse,
    dependencies=[Depends(require_user_role(app_settings.ADMIN_ROLE))],
)
async def update_external_vector_map(
    vector_map_id: uuid.UUID,
    updated_vector_map: VectorMapExternalPayload,
    session: Session = Depends(get_session),
    http_client: AsyncClient = Depends(get_http_client),
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
):
    vector_map = get_vector_map(vector_map_id, session)

    vector_map.title = updated_vector_map.title
    vector_map.description = updated_vector_map.description
    vector_map.link_thumb = updated_vector_map.link_thumb
    vector_map.link_content = updated_vector_map.link_content
    vector_map.content_type = updated_vector_map.content_type
    vector_map.time_period = updated_vector_map.time_period

    vector_map.last_change = datetime.now()

    geojson = await fetch_and_validate_geojson(vector_map.link_content, http_client)

    session.add(vector_map)
    session.commit()

    await push_vector_map_to_index(
        vector_map, geojson.model_dump_json(exclude_unset=True), es_index
    )

    return VectorMapExternalResponse(
        id=vector_map.public_id,
        title=vector_map.title,
        description=vector_map.description,
        link_thumb=vector_map.link_thumb,
        link_content=vector_map.link_content,
        content_type=vector_map.content_type,
        time_period=vector_map.time_period,
        submitted=vector_map.submitted,
        last_change=vector_map.last_change,
    )


@router.delete(
    "/{vector_map_id}",
    tags=["vector_map_external"],
    response_model=VectorMapExternalIdResponse,
    dependencies=[Depends(require_user_role(app_settings.ADMIN_ROLE))],
)
async def delete_external_vector_map(
    vector_map_id: uuid.UUID,
    session: Session = Depends(get_session),
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
):
    vector_map = get_vector_map(vector_map_id, session)

    session.delete(vector_map)
    session.commit()

    await es_index.delete(
        index=app_settings.ES_INDEX_NAME, doc_type=None, id=str(vector_map.public_id)
    )

    return {"id": vector_map_id}


@router.post(
    "/refresh_search_index/{vector_map_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["vector_map_external"],
    dependencies=[Depends(require_user_role(app_settings.ADMIN_ROLE))],
)
async def refresh_search_index(
    vector_map_id: uuid.UUID,
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
    http_client: AsyncClient = Depends(get_http_client),
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    geojson = await fetch_and_validate_geojson(vector_map.link_content, http_client)

    await push_vector_map_to_index(
        vector_map, geojson.model_dump_json(exclude_unset=True), es_index
    )

    return Response(status_code=204)

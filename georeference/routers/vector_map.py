#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 08.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import uuid
from datetime import datetime
from typing import Annotated, List, Union

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, HTTPException, Response
from loguru import logger
from pyproj import Geod
from shapely import Polygon
from shapely.io import from_geojson
from shapely.lib import is_empty
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from starlette import status

from georeference.config.db import get_session
from georeference.config.settings import get_settings, Settings
from georeference.models.vector_map import (
    VectorMap,
    VectorMapContent,
    RoleEnum,
    VectorMapRoles,
)
from georeference.models.vector_map_external import VectorMapExternal
from georeference.schemas.user import User
from georeference.schemas.vector_map import (
    VectorMapPayload,
    VectorMapResponse,
    VectorMapMetadata,
    VectorMapVersionsResponse,
    VectorMapRolePayload,
    VectorMapRemoveRolePayload,
    VectorMapVersionCreateResponse,
    VectorMapVersionResponse,
    VectorMapCreateResponse,
    VectorMapResponsePublic,
    VectorMapUpdatePayload,
    VectorMapVersionPayload,
    VectorMapUpdateRolesPayload,
)
from georeference.utils.auth import (
    require_user_role,
    get_user_from_session,
    is_admin,
    is_editor,
)
from georeference.utils.es_index.document_formatter import (
    generate_es_vector_map_document,
)
from georeference.utils.es_index.es_index_async import get_async_es_client
from georeference.utils.utils import bounds_to_polygon

router = APIRouter()
settings = get_settings()


def create_geodesic_rectangle(point, distance_meters):
    """
    Create a rectangle around a point in WGS84, with corners at specified meter distance.

    :param point: Shapely Point in WGS84 (lon, lat)
    :param distance_meters: Distance from center to each corner
    :return: Shapely Polygon representing the rectangle
    """
    geod = Geod(ellps="WGS84")

    corners = []
    for angle in [45, 135, 225, 315]:
        lon, lat, _ = geod.fwd(point.x, point.y, angle, distance_meters)
        corners.append((lon, lat))

    return Polygon(corners)


def get_vector_map(vector_map_id: uuid.UUID, session: Session) -> VectorMap:
    vector_map = VectorMap.by_public_id(vector_map_id, session)

    if vector_map is None:
        raise HTTPException(status_code=404, detail="Vector map not found")

    return vector_map


world_bounds = ((180, 90), (-180, 90), (-180, -90), (180, -90), (180, 90))


async def push_vector_map_to_index(
    vector_map: VectorMap | VectorMapExternal,
    geom_string: str,
    es_index: AsyncElasticsearch,
):
    exists_index = await es_index.indices.exists(index=settings.ES_INDEX_NAME)
    if exists_index:
        geom = from_geojson(geom_string)

        # In case the geometry is empty, assume the world bounds (because an empty geometry would never show up)
        if is_empty(geom):
            geom = Polygon(world_bounds)
        # In case the geometry is a single point or a single point in a collection, create a rectangle around it
        elif geom.geom_type == "Point" or (
            geom.geom_type == "GeometryCollection"
            and len(geom.geoms) == 1
            and geom.geoms[0].geom_type == "Point"
        ):
            if geom.geom_type == "GeometryCollection":
                geom = create_geodesic_rectangle(geom.geoms[0], 1000)
            else:
                geom = create_geodesic_rectangle(geom, 1000)

        logger.debug(geom_string)
        logger.debug(geom)
        logger.debug(bounds_to_polygon(geom.bounds))

        await es_index.index(
            index=settings.ES_INDEX_NAME,
            doc_type=None,
            id=str(vector_map.public_id),
            document=generate_es_vector_map_document(
                vector_map, bounds_to_polygon(geom.bounds)
            ),
        )
    else:
        logger.error(
            f"Failed to push vector map {vector_map.id} to index: Index {settings.ES_INDEX_NAME} does not exist."
        )


@router.get(
    "/{vector_map_id}",
    tags=["vector_map"],
    response_model=Union[VectorMapResponse, VectorMapResponsePublic],
)
def read_vector_map(
    vector_map_id: uuid.UUID,
    user: User = Depends(get_user_from_session),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    vector_map, vector_map_contents = VectorMap.by_public_id_with_contents(
        vector_map_id, session
    )

    if vector_map is None:
        raise HTTPException(status_code=404, detail="Vector map not found")

    user_role = None

    if user is not None:
        # Admins own everything
        if is_admin(user, settings):
            user_role = RoleEnum.owner

        # If user has editor role, check if the user has a role for this vector map
        elif is_editor(user, settings):
            vector_map_role = VectorMapRoles.by_vector_map_id_and_user_id(
                vector_map.id, user.username, session
            )

            if vector_map_role is not None:
                user_role = vector_map_role.role

    # Return response
    response = VectorMapResponse(
        title=vector_map.title,
        description=vector_map.description,
        link_thumb=vector_map.link_thumb,
        id=vector_map.public_id,
        submitted=vector_map.submitted,
        last_change=vector_map.last_change,
        geojson=vector_map_contents.content,
        version=vector_map_contents.version,
        user_role=user_role,
    )

    # Update telemetry
    vector_map.request_count += 1
    vector_map.last_request = datetime.now()
    session.add(vector_map)
    session.commit()

    return (
        response
        if user_role is not None
        else VectorMapResponse.to_public_response(response)
    )


@router.post(
    "/", status_code=201, tags=["vector_map"], response_model=VectorMapCreateResponse
)
async def create_new_vector_map(
    new_vector_map: VectorMapPayload,
    user: Annotated[User, Depends(require_user_role(settings.EDITOR_ROLE))],
    session: Session = Depends(get_session),
    es_index=Depends(get_async_es_client),
):
    user_id = user.username

    submitted = datetime.now()

    vector_map = VectorMap(
        title=new_vector_map.title,
        description=new_vector_map.description,
        link_thumb=new_vector_map.link_thumb,
        submitted=submitted,
        last_change=submitted,
    )

    session.add(vector_map)
    session.flush()

    vector_map_content = VectorMapContent(
        vector_map_id=vector_map.id,
        content=new_vector_map.geojson.model_dump(exclude_unset=True),
        version=0,
        submitted=submitted,
        created_by=user_id,
    )

    session.add(vector_map_content)

    vector_map_role = VectorMapRoles(
        vector_map_id=vector_map.id,
        user_id=user_id,
        role=RoleEnum.owner,
    )

    session.add(vector_map_role)

    session.commit()

    session.refresh(vector_map)

    await push_vector_map_to_index(
        vector_map, new_vector_map.geojson.model_dump_json(exclude_unset=True), es_index
    )

    return {"id": vector_map.public_id}


@router.put(
    "/{vector_map_id}",
    tags=["vector_map"],
    responses={
        200: {"description": "Vector map successfully updated", "content": None}
    },
)
async def update_vector_map_metadata(
    updated_vector_map: VectorMapMetadata,
    vector_map_id: uuid.UUID,
    user: Annotated[User, Depends(require_user_role(settings.EDITOR_ROLE))],
    session: Session = Depends(get_session),
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMap.is_owner(vector_map.id, user, session):
        raise HTTPException(
            status_code=403, detail="User is not allowed to update this vector map"
        )

    submitted = datetime.now()

    vector_map.title = updated_vector_map.title
    vector_map.description = updated_vector_map.description
    vector_map.link_thumb = updated_vector_map.link_thumb

    vector_map.last_change = submitted

    session.add(vector_map)
    session.commit()

    vector_map_content = VectorMapContent.get_entity_for_most_recent_version(
        vector_map.id, session
    )

    await push_vector_map_to_index(
        vector_map,
        json.dumps(vector_map_content.content),
        es_index,
    )

    return Response(status_code=200)


@router.delete(
    "/{vector_map_id}",
    tags=["vector_map"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Vector map successfully deleted", "content": None}
    },
)
async def delete_vector_map(
    vector_map_id: uuid.UUID,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMap.is_owner(vector_map.id, user, session):
        raise HTTPException(
            status_code=403, detail="User is not allowed to delete this vector map"
        )

    session.delete(vector_map)
    session.commit()

    # Delete document from index
    await es_index.delete(
        index=settings.ES_INDEX_NAME, doc_type=None, id=vector_map.public_id
    )

    return Response(status_code=204)


# @TODO: Add tests
@router.patch("/{vector_map_id}", tags=["vector_map"])
async def update_vector_map(
    vector_map_update: VectorMapUpdatePayload,
    vector_map_id: uuid.UUID,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
):
    vector_map = get_vector_map(vector_map_id, session)

    metadata_update = vector_map_update.metadata
    vector_map_content = None

    if metadata_update is not None:
        if not VectorMap.is_owner(vector_map.id, user, session):
            raise HTTPException(
                status_code=403, detail="User is not allowed to update this vector map"
            )

        submitted = datetime.now()

        vector_map.title = metadata_update.title
        vector_map.description = metadata_update.description
        vector_map.link_thumb = metadata_update.link_thumb

        vector_map.last_change = submitted

        session.add(vector_map)

    if vector_map_update.geojson is not None:
        if not VectorMapRoles.is_user_allowed_to_edit(vector_map.id, user, session):
            raise HTTPException(
                status_code=403, detail="User is not allowed to edit this vector map"
            )

        most_recent_version = VectorMapContent.get_most_recent_version(
            vector_map.id, session
        )

        base_version = vector_map_update.current_version
        if most_recent_version != base_version:
            raise HTTPException(
                status_code=409, detail="Version does not match most recent version"
            )

        vector_map_content = VectorMapContent(
            vector_map_id=vector_map.id,
            content=vector_map_update.geojson.model_dump(exclude_unset=True),
            version=most_recent_version + 1,
            submitted=datetime.now(),
            created_by=user.username,
        )

        session.add(vector_map_content)

    session.commit()

    if vector_map_content is None:
        vector_map_content = VectorMapContent.get_entity_for_most_recent_version(
            vector_map.id, session
        )

    await push_vector_map_to_index(
        vector_map,
        json.dumps(vector_map_content.content),
        es_index,
    )

    return {"version": vector_map_content.version}


@router.get(
    "/{vector_map_id}/versions",
    tags=["vector_map"],
    response_model=VectorMapVersionsResponse,
)
def get_vector_map_versions(
    vector_map_id: uuid.UUID,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMapRoles.is_user_allowed_to_edit(vector_map.id, user, session):
        raise HTTPException(
            status_code=403, detail="User is not allowed to view previous versions"
        )

    return VectorMapContent.get_versions(vector_map.id, session)


@router.get(
    "/{vector_map_id}/versions/{version}",
    tags=["vector_map"],
    response_model=VectorMapVersionResponse,
)
def get_vector_map_version(
    vector_map_id: uuid.UUID,
    version: int,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMapRoles.is_user_allowed_to_edit(vector_map.id, user, session):
        raise HTTPException(status_code=404, detail="Entity not found")

    vector_map_content = VectorMapContent.get_version(vector_map.id, version, session)

    if vector_map_content is None:
        raise HTTPException(status_code=404, detail="Vector map version not found")

    return VectorMapContent.to_public(vector_map_content)


@router.post(
    "/{vector_map_id}/versions",
    status_code=201,
    tags=["vector_map"],
    response_model=VectorMapVersionCreateResponse,
)
async def create_vector_map_version(
    new_vector_map_content: VectorMapVersionPayload,
    vector_map_id: uuid.UUID,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
    es_index: AsyncElasticsearch = Depends(get_async_es_client),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMapRoles.is_user_allowed_to_edit(vector_map.id, user, session):
        raise HTTPException(
            status_code=403, detail="User is not allowed to edit this vector map"
        )

    submitted = datetime.now()

    most_recent_version = VectorMapContent.get_most_recent_version(
        vector_map.id, session
    )

    base_version = new_vector_map_content.current_version

    if most_recent_version != base_version:
        raise HTTPException(
            status_code=409, detail="Version does not match most recent version"
        )

    vector_map_content = VectorMapContent(
        vector_map_id=vector_map.id,
        content=new_vector_map_content.geojson.model_dump(),
        version=most_recent_version + 1,
        submitted=submitted,
        created_by=user.username,
    )

    session.add(vector_map_content)

    vector_map.last_change = submitted
    session.add(vector_map)

    session.commit()

    await push_vector_map_to_index(
        vector_map,
        new_vector_map_content.geojson.model_dump_json(exclude_unset=True),
        es_index,
    )

    return {"version": vector_map_content.version}


@router.get(
    "/{vector_map_id}/roles",
    tags=["vector_map"],
    response_model=List[VectorMapRolePayload],
)
def get_roles(
    vector_map_id: uuid.UUID,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMap.is_owner(vector_map.id, user, session):
        raise HTTPException(
            status_code=403, detail="User is not allowed to view this vector map"
        )

    return list(
        map(
            VectorMapRoles.to_public,
            VectorMapRoles.by_vector_map_id(vector_map.id, session),
        )
    )


@router.patch(
    "/{vector_map_id}/roles",
    tags=["vector_map"],
    responses={200: {"description": "Roles successfully updated", "content": None}},
)
def update_roles(
    vector_map_id: uuid.UUID,
    new_roles: VectorMapUpdateRolesPayload,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    # Check that the user is allowed to edit the roles
    if not VectorMap.is_owner(vector_map.id, user, session):
        raise HTTPException(
            status_code=403,
            detail="User is not allowed to edit the roles of this vector map",
        )

    # Check a user is not added and removed in the same request
    modified_users = set([])

    if new_roles.create_or_update is not None:
        for role in new_roles.create_or_update:
            if role.user_id in modified_users:
                raise HTTPException(
                    status_code=409,
                    detail=f"The user {role.user_id} appears multiple times",
                )

            modified_users.add(role.user_id)

    if new_roles.remove is not None:
        for role in new_roles.remove:
            if role.user_id in modified_users:
                raise HTTPException(
                    status_code=409,
                    detail=f"The user {role.user_id} appears multiple times",
                )

            modified_users.add(role.user_id)

    # Handle add roles
    if new_roles.create_or_update is not None:
        for role in new_roles.create_or_update:
            if role.role == RoleEnum.owner and not is_admin(user, settings):
                raise HTTPException(
                    status_code=403, detail="Only admins can modify owners"
                )

            vector_map_role = VectorMapRoles.by_vector_map_id_and_user_id(
                vector_map.id, role.user_id, session
            )

            if vector_map_role is None:
                # If the user does not have a role for this vector map, create a new role
                vector_map_role = VectorMapRoles(
                    vector_map_id=vector_map.id,
                    user_id=role.user_id,
                    role=role.role,
                )

            else:
                # If the user already has a role for this vector map, update the role
                vector_map_role.role = role.role

            try:
                session.add(vector_map_role)
                session.flush()
            except IntegrityError:
                raise HTTPException(
                    status_code=409,
                    detail=f"User {role.user_id} already has a role for this vector map",
                )

    # Handle remove roles
    if new_roles.remove is not None:
        for role in new_roles.remove:
            to_delete = VectorMapRoles.by_vector_map_id_and_user_id(
                vector_map.id, role.user_id, session
            )

            if to_delete is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"No role found for the supplied user {role.user_id}",
                )

            if to_delete.role == RoleEnum.owner and not is_admin(user, settings):
                raise HTTPException(
                    status_code=403, detail="Only admins can modify owners"
                )

            session.delete(to_delete)
            session.flush()

    session.commit()


@router.post(
    "/{vector_map_id}/roles/add",
    tags=["vector_map"],
    responses={200: {"description": "Role successfully added", "content": None}},
)
def set_roles(
    vector_map_id: uuid.UUID,
    new_role: VectorMapRolePayload,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMap.is_owner(vector_map.id, user, session):
        raise HTTPException(
            status_code=403, detail="User is not allowed to edit this vector map"
        )

    if new_role.role == RoleEnum.owner and not is_admin(user, settings):
        raise HTTPException(status_code=403, detail="Only admins can modify owners")

    vector_map_role = VectorMapRoles(
        vector_map_id=vector_map.id,
        user_id=new_role.user_id,
        role=new_role.role,
    )

    try:
        session.add(vector_map_role)
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User already has a role for this vector map"
        )

    return Response(status_code=200)


@router.post(
    "/{vector_map_id}/roles/remove",
    tags=["vector_map"],
    responses={200: {"description": "Role successfully removed", "content": None}},
)
def remove_role(
    vector_map_id: uuid.UUID,
    new_role: VectorMapRemoveRolePayload,
    user: User = Depends(require_user_role(settings.EDITOR_ROLE)),
    session: Session = Depends(get_session),
):
    vector_map = get_vector_map(vector_map_id, session)

    if not VectorMap.is_owner(vector_map.id, user, session):
        raise HTTPException(
            status_code=403, detail="User is not allowed to edit this vector map"
        )

    to_delete = VectorMapRoles.by_vector_map_id_and_user_id(
        vector_map.id, new_role.user_id, session
    )

    if to_delete is None:
        raise HTTPException(status_code=404, detail="No role found for this user")

    if to_delete.role == RoleEnum.owner and not is_admin(user, settings):
        raise HTTPException(status_code=403, detail="Only admins can modify owners")

    session.delete(to_delete)
    session.commit()

    return Response(status_code=200)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 08.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import enum
import uuid
from typing import Optional, Dict

from pydantic import NaiveDatetime
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlmodel import Field, SQLModel, select, col, desc

from georeference.config.settings import get_settings
from georeference.models import datetime_without_timezone
from georeference.schemas.user import User
from georeference.utils.auth import is_admin


class RoleEnum(enum.Enum):
    owner = "owner"
    editor = "editor"


class VectorMap(SQLModel, table=True):
    __tablename__ = "vector_maps"

    id: int = Field(primary_key=True, default=None)
    public_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Field(UUID(as_uuid=True), unique=True, nullable=False),
    )
    description: Optional[str]
    title: str
    link_thumb: Optional[str]
    submitted: NaiveDatetime = datetime_without_timezone
    last_change: NaiveDatetime = datetime_without_timezone

    request_count: int = Field(default=0)
    last_request: Optional[NaiveDatetime] = datetime_without_timezone

    @classmethod
    def all(cls, session):
        return session.exec(select(VectorMap)).all()

    @classmethod
    def all_with_content(cls, session):
        # Create a subquery with row numbers
        subquery = select(
            VectorMapContent,
            func.row_number()
            .over(
                partition_by=VectorMapContent.vector_map_id,
                order_by=desc(VectorMapContent.version),
            )
            .label("row_number"),
        ).subquery()

        # Main query joining with A and filtering for row_number = 1
        query = (
            select(VectorMap, subquery)
            .join(subquery, VectorMap.id == subquery.c.vector_map_id)
            .where(subquery.c.row_number == 1)
        )

        entries = session.exec(query).all()

        response = []
        for entry in entries:
            vector_map = entry[0]
            vector_map_content = VectorMapContent(
                vector_map_id=entry[1],
                content=entry[2],
                version=entry[3],
                submitted=entry[4],
            )
            response.append((vector_map, vector_map_content))
        return response

    @classmethod
    def by_public_id(cls, public_id: uuid.UUID, session) -> "VectorMap":
        return session.exec(
            select(VectorMap).where(col(VectorMap.public_id) == public_id)
        ).first()

    @classmethod
    def by_public_id_with_contents(cls, public_id: uuid.UUID, session):
        return session.exec(
            select(VectorMap, VectorMapContent)
            .where(col(VectorMap.id) == col(VectorMapContent.vector_map_id))
            .where(col(VectorMap.public_id) == public_id)
            .order_by(VectorMapContent.version.desc())
            .limit(1)
        ).first()

    @classmethod
    def is_owner(cls, vector_map_id: int, user: User, session):
        user_id = user.username

        # admins own everything
        user_is_admin = is_admin(user, get_settings())

        if user_is_admin:
            return True

        # else check if the user is owner
        result = session.exec(
            select(VectorMapRoles)
            .where(col(VectorMapRoles.vector_map_id) == vector_map_id)
            .where(col(VectorMapRoles.user_id) == user_id)
            .where(col(VectorMapRoles.role) == RoleEnum.owner)
        ).first()

        return result is not None


class VectorMapContent(SQLModel, table=True):
    __tablename__ = "vector_maps_content"

    vector_map_id: int = Field(
        default=None, primary_key=True, foreign_key="vector_maps.id"
    )
    content: Dict = Field(sa_type=JSONB)
    version: int = Field(default=0, primary_key=True)
    submitted: NaiveDatetime = datetime_without_timezone
    created_by: str = Field(default=None)

    @classmethod
    def get_versions(cls, vector_map_id: int, session):
        results = session.exec(
            select(
                VectorMapContent.version,
                VectorMapContent.submitted,
                VectorMapContent.created_by,
            )
            .where(VectorMapContent.vector_map_id == vector_map_id)
            .order_by(VectorMapContent.version.desc())
        ).all()

        columns = ["version", "submitted", "created_by"]

        # Convert list of tuples [(version, submitted), ...] to list of dicts
        return [dict(zip(columns, result)) for result in results]

    @classmethod
    def get_entity_for_most_recent_version(cls, vector_map_id: int, session):
        return session.exec(
            select(VectorMapContent)
            .where(VectorMapContent.vector_map_id == vector_map_id)
            .order_by(VectorMapContent.version.desc())
            .limit(1)
        ).one()

    @classmethod
    def get_most_recent_version(cls, vector_map_id: int, session):
        return session.exec(
            select(VectorMapContent.version)
            .where(VectorMapContent.vector_map_id == vector_map_id)
            .order_by(VectorMapContent.version.desc())
            .limit(1)
        ).one()

    @classmethod
    def get_version(cls, vector_map_id: int, version: int, session):
        return session.exec(
            select(VectorMapContent)
            .where(VectorMapContent.vector_map_id == vector_map_id)
            .where(VectorMapContent.version == version)
        ).first()

    @classmethod
    def to_public(cls, vector_map_content: "VectorMapContent"):
        result_dict = vector_map_content.model_dump(exclude={"vector_map_id"})
        result_dict["geojson"] = result_dict.pop("content")
        return result_dict


class VectorMapRoles(SQLModel, table=True):
    __tablename__ = "vector_maps_roles"

    vector_map_id: int = Field(
        default=None, primary_key=True, foreign_key="vector_maps.id"
    )
    role: RoleEnum = Field(default=RoleEnum.editor)
    user_id: str = Field(primary_key=True)

    @classmethod
    def by_vector_map_id(cls, vector_map_id: int, session):
        return session.exec(
            select(VectorMapRoles).where(
                col(VectorMapRoles.vector_map_id) == vector_map_id
            )
        ).all()

    @classmethod
    def by_vector_map_id_and_user_id(cls, vector_map_id: int, user_id: str, session):
        return session.exec(
            select(VectorMapRoles)
            .where(col(VectorMapRoles.vector_map_id) == vector_map_id)
            .where(col(VectorMapRoles.user_id) == user_id)
        ).first()

    @classmethod
    def is_user_allowed_to_edit(cls, vector_map_id: int, user: User, session):
        user_id = user.username

        # admins can do everything
        user_is_admin = is_admin(user, get_settings())

        if user_is_admin:
            return True

        # else check if the user is owner
        result = VectorMapRoles.by_vector_map_id_and_user_id(
            vector_map_id, user_id, session
        )

        if result is None:
            return False

        return result.role == RoleEnum.owner or result.role == RoleEnum.editor

    @classmethod
    def to_public(cls, vector_map_role: "VectorMapRoles"):
        return vector_map_role.model_dump(exclude={"vector_map_id"})

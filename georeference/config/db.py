#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from sqlmodel import create_engine, Session

from georeference.config.settings import get_settings, Settings


def settings_to_db_dict(settings: Settings):
    return settings.model_dump(
        include={
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
        }
    )


def get_database_url_from_settings(settings: dict):
    return f"postgresql://{settings['POSTGRES_USER']}:{settings['POSTGRES_PASSWORD']}@{settings['POSTGRES_HOST']}:{settings['POSTGRES_PORT']}/{settings['POSTGRES_DB']}"


def get_database_engine(settings_override: dict = None):
    """
    Get the database engine, based on the default configuration from settings and optional overrides.
    """
    global_settings = get_settings()

    base_settings = settings_to_db_dict(global_settings)

    settings = base_settings

    if settings_override:
        settings = settings | settings_override

    database_url = get_database_url_from_settings(settings)

    db_engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
    )
    return db_engine


engine = get_database_engine()


def get_session():
    with Session(engine) as session:
        yield session

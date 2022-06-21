#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 12.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.settings import TEMPLATE_PUBLIC_MAP_ID, TEMPLATE_PUBLIC_MOSAIC_MAP_ID
from georeference.utils.parser import from_public_map_id, from_public_mosaic_map_id, to_public_map_id, to_public_mosaic_map_id


def test_to_public_id_success():
    # Check if it returns the correct id
    assert to_public_map_id(1) == TEMPLATE_PUBLIC_MAP_ID.format(1)


def test_to_public_mosaic_id_success():
    # Check if it returns the correct id
    assert to_public_mosaic_map_id(1) == TEMPLATE_PUBLIC_MOSAIC_MAP_ID.format(1)


def test_from_public_map_id_success():
    # Check for proper resolving of a public oai
    assert from_public_map_id(TEMPLATE_PUBLIC_MAP_ID.format(1)) == 1


def test_from_public_mosaic_map_id_success():
    # Check for proper resolving of a public oai
    assert from_public_mosaic_map_id(TEMPLATE_PUBLIC_MOSAIC_MAP_ID.format('1')) == 1
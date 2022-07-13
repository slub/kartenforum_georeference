#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 12.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.settings import TEMPLATE_OAI_ID
from georeference.utils.parser import from_public_oai
from georeference.utils.parser import to_public_oai


def test_to_public_oai_success():
    # Check if it returns the correct id
    assert to_public_oai(1) == TEMPLATE_OAI_ID.format(1)


def test_from_public_oai_success():
    # Check for proper resolving of a public oai
    assert from_public_oai(TEMPLATE_OAI_ID.format(1)) == 1

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 12.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.settings import TEMPLATE_OAI_ID
from georeference.utils.parser import fromPublicOAI
from georeference.utils.parser import toPublicOAI

def test_toPublicOAI_success():
    # Check if it returns the correct id
    assert toPublicOAI(1) == TEMPLATE_OAI_ID % 1

def test_fromPublicOAI_success():
    # Check for proper resolving of a public oai
    assert fromPublicOAI(TEMPLATE_OAI_ID % 1) == 1
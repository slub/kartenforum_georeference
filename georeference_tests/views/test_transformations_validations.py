#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import json
from datetime import datetime
from georeference.models.original_maps import OriginalMap
from georeference.models.jobs import Job, TaskValues
from georeference.settings import ROUTE_PREFIX

def test_GET_TransformationsForValidation_success_emptyResult(testapp):
    res = testapp.get(ROUTE_PREFIX + '/transformations/validations/%s' % 'test', status=400)
    assert res.status_int == 400

def test_GET_TransformationsForValidation_validation_missing(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + '/transformations/validations/%s' % 'MISSING', status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 4

def test_GET_TransformationsForValidation_validation_valid(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + '/transformations/validations/%s' % 'valid', status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 18

def test_GET_TransformationsForValidation_validation_invalid(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + '/transformations/validations/%s' % 'invalid', status=200)
    assert res.status_int == 200
    assert len(res.json['transformations']) == 1






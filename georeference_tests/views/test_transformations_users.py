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

def test_GET_TransformationsForUserId_success_emptyResult(testapp):
    res = testapp.get(ROUTE_PREFIX + '/transformations/users/%s' % 'test', status=200)
    assert res.status_int == 200
    assert len(res.json['items']) == 0

def test_GET_TransformationsForUserId_success_transformationResults(testapp, dbsession):
    res = testapp.get(ROUTE_PREFIX + '/transformations/users/%s' % 'user_1', status=200)
    assert res.status_int == 200
    assert len(res.json['items']) == 18

    dbsession.rollback()








#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from setuptools import setup, find_packages

requires = [
    'pyramid==2.0',
    'pyramid_tm==2.4',
    'psycopg2==2.9.1',
    'SQLAlchemy==1.4.23',
    'waitress==2.0'
]

setup(
    name='georeference',
    version='1.0',
    description='georeference',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    message_extractors={
        'georeference': [
            ('**.py', 'python', None),
        ]
    },
    author='Jacob Mendt, Nicolas Looschen',
    author_email='jacob.mendt@pikobytes.de,nicolas.looschen@pikobytes.de',
    url='http://www.slub-dresden.de/startseite/',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    test_suite="georeference",
    entry_points="""\
      [paste.app_factory]
      main = georeference:main
      """,
)

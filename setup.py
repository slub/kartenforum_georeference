#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from setuptools import setup, find_packages

requires = [
    'elasticsearch==7.14.1',
    'GDAL==3.2.2',
    'jsonschema==4.4.0',
    'pillow==8.3.2',
    'python-daemon==2.3.0',
    'pyramid==2.0',
    'pyramid_tm==2.4',
    'pyramid_retry==2.1.1',
    'pyproj==3.3.1',
    'psycopg2==2.9.1',
    'shapely==1.8.2',
    'SQLAlchemy==1.4.23',
    'uwsgi==2.0.20',
    'waitress==2.0',
    'zope.sqlalchemy==1.5'
]

tests_require = [
    'WebTest',
    'pytest',
    'pytest-cov',
]

setup(
    name='georeference',
    version='1.1',
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
    packages=find_packages(exclude=['georeference_tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require={
        'testing': tests_require,
    },
    entry_points="""\
      [paste.app_factory]
      main = georeference:main
      """,
)

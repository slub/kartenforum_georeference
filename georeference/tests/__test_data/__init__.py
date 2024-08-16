#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 14.08.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package


geojson_layer_test_data = {
    "id": "test",
    "isVisible": True,
    "opacity": 1,
    "properties": {
        "has_georeference": True,
        "title": "test",
        "time_changed": "14. August 2024",
    },
    "geojson": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [13.804741932911439, 51.08779410177894],
                        [13.78840428422899, 51.04284386221306],
                    ],
                },
                "properties": {
                    "stroke": "#00FF00",
                    "stroke-opacity": 1,
                    "stroke-width": 1,
                },
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.809511859826586, 51.04846570158696],
                },
                "properties": {"img_link": "test", "marker": "blue"},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [13.582117114190424, 51.10333679209185],
                            [13.582117114190424, 51.05633111411615],
                            [13.651700711913037, 51.05633111411615],
                            [13.651700711913037, 51.10333679209185],
                            [13.582117114190424, 51.10333679209185],
                        ]
                    ],
                },
                "properties": {
                    "fill": "#0000FF",
                    "fill-opacity": 0.13,
                    "stroke": "#0000FF",
                    "stroke-opacity": 1,
                    "stroke-width": 3,
                },
            },
        ],
    },
    "type": "geojson",
}

historic_map_layer_test_data = {
    "id": "oai:de:slub-dresden:vk:id-10009466",
    "isVisible": True,
    "opacity": 1,
    "properties": {
        "geometry": {
            "disposed": False,
            "pendingRemovals_": None,
            "dispatching_": None,
            "listeners_": {"change": [None]},
            "revision_": 1,
            "ol_uid": "52",
            "values_": None,
            "extent_": [None, None, None, None],
            "extentRevision_": -1,
            "simplifiedGeometryMaxMinSquaredTolerance": 0,
            "simplifiedGeometryRevision": 0,
            "layout": "XY",
            "stride": 2,
            "flatCoordinates": [
                1528079.6517287816,
                6639788.6272049155,
                1523588.9457691766,
                6634504.99075245,
                1521067.4031214635,
                6631593.357984335,
                1529222.4626306428,
                6624434.406758923,
                1535185.1875165382,
                6631367.387579373,
                1535911.6425947682,
                6632207.58598983,
                1535948.6670121283,
                6632251.1784248585,
                1536257.7016071167,
                6632615.443591013,
                1528079.6517287816,
                6639788.6272049155,
            ],
            "ends_": [18],
            "flatInteriorPointRevision_": -1,
            "flatInteriorPoint_": None,
            "maxDelta_": -1,
            "maxDeltaRevision_": -1,
            "orientedRevision_": -1,
            "orientedFlatCoordinates_": None,
        },
        "map_id": "oai:de:slub-dresden:vk:id-10009466",
        "file_name": "df_dk_0000006",
        "description": "Karte des Elbstromes innerhalb des Königreichs Sachsen : mit Angabe des durch das Hochwasser vom 31sten März 1845 erreichten Ueberschwemmungsgebietes , ... in 15 Sectionen und mit den von der Königlichen Wasserbau-Direction aufgenommenen Stromprofilen und Wassertiefen / bearb. von dem Königlich Sächsischen Finanzvermessungs-Bureau. [Lith. von W. Werner]. - 1:12 000 Dresden : Meinhold , 1850-1855. - 1 Kt. auf 15 Bl. : mehrfarb. , je Bl. 63 x 61 cm Nebensacht.: Karte des Elbstromes in Sachsen mit der Fluth 1845. - Lithogr. - Enth.: Sect. 1, Titelbl. mit Verbindungsnetz. Sect. 2/15, Kartenwerk. - Mit Höhenlage der Elb-Pegel und Brückenquerschnitten",
        "map_scale": 12000,
        "zoomify_url": "https://fotothek.slub-dresden.de/zooms/df/dk/0000000/df_dk_0000006/ImageProperties.xml",
        "map_type": "tkx",
        "keywords": "Druckgrafik\n                    ;",
        "title_long": "Sect. 09: Dresden",
        "title": "Dresden",
        "permalink": "https://www.deutschefotothek.de/documents/obj/70400017/df_dk_00000063",
        "slub_url": "https://www.deutschefotothek.de/documents/obj/70400017/df_dk_00000063",
        "online_resources": [
            {
                "url": "https://www.deutschefotothek.de/documents/obj/70400017/df_dk_00000063",
                "type": "Permalink",
            },
            {
                "url": "https://wms-slub.pikobytes.de/map/10009466?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities",
                "type": "WMS",
            },
            {
                "url": "https://wcs-slub.pikobytes.de/map/10009466?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCapabilities",
                "type": "WCS",
            },
            {
                "url": "https://wcs-slub.pikobytes.de/map/10009466?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCoverage&CoverageID=df_dk_0000006&CRS=EPSG:4314&BBOX=13.665740962966385,51.01898159252702,13.802218747720001,51.105679277365006&WIDTH=12942&HEIGHT=8221&FORMAT=GEOTIFF",
                "type": "download",
            },
        ],
        "tms_urls": ["https://tms.ddev.site/tkx/df_dk_0000006"],
        "thumb_url": "https://fotothek.slub-dresden.de/thumbs/df/dk/0000000/df_dk_0000006.jpg",
        "has_georeference": True,
        "time_published": "1855",
        "type": "single_sheet",
        "id": "oai:de:slub-dresden:vk:id-10009466",
    },
    "coordinates": [
        [
            [1528079.6517287816, 6639788.6272049155],
            [1523588.9457691766, 6634504.99075245],
            [1521067.4031214635, 6631593.357984335],
            [1529222.4626306428, 6624434.406758923],
            [1535185.1875165382, 6631367.387579373],
            [1535911.6425947682, 6632207.58598983],
            [1535948.6670121283, 6632251.1784248585],
            [1536257.7016071167, 6632615.443591013],
            [1528079.6517287816, 6639788.6272049155],
        ]
    ],
    "type": "historic_map",
}

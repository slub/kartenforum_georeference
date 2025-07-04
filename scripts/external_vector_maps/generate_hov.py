"""
Created by tom.schulze@pikobytes.de on 02.07.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.


Usage: export HOV_API_TOKEN=XXXX; python generate_hov.py > hov.json
"""

import json
import sys
import requests
import os

USER_AGENT = "Pikobytes HOV-Bot/1.0 (https://pikobytes.de; info@pikobytes.de)"
HOV_API_BASE_URL = "https://db.isgv.de/items/hov_orte"
HOV_API_TOKEN = os.environ.get("HOV_API_TOKEN")
HOV_WEB_BASE_URL = "https://hov.isgv.de/"

WD_BASE_URL = "https://query.wikidata.org/sparql"


# 1: Wüstung
# 2: ehemalige Wüstung
# 3: fragliche Wüstung
# 4: Stadt
MARKER = {1: "#695cf2", 2: "#aaa3f8", 3: "#f2695c", 4: "#00927e"}
MARKER_DEFAULT = "#ACACAC55"


def get_marker_color(record):
    try:
        type_id = record["typ"]["id"]
        return MARKER[type_id]
    except Exception:
        return MARKER_DEFAULT


def get_type_name(record):
    try:
        # SIC!
        type_name = record["typ"]["ortsyp"]
        return type_name
    except Exception:
        return None


def validate_geometry(geometry):
    valid_geometries = ["Point", "LineString", "Polygon"]

    if geometry is None:
        raise ValueError("Geometry is None")

    if geometry["type"] not in valid_geometries:
        raise ValueError("Invalid geometry")

    if geometry["coordinates"][0] < 11 or geometry["coordinates"][0] > 16:
        raise ValueError("Invalid longitude")

    if geometry["coordinates"][1] < 50 or geometry["coordinates"][1] > 52:
        raise ValueError("Invalid latitude")

    return


def create_feature(record):
    hov_code = record["hovcode"]
    geometry = record["geometry"]
    title = record["ortsname"]
    hov_link = HOV_WEB_BASE_URL + str(hov_code)
    marker = get_marker_color(record)
    type_name = get_type_name(record)
    image_url = record["image_url"]

    validate_geometry(geometry)

    feature = {}
    feature["properties"] = {}

    feature["id"] = hov_code
    feature["geometry"] = geometry
    feature["type"] = "Feature"

    if image_url is not None:
        feature["properties"]["img_link"] = image_url

    feature["properties"]["marker"] = marker

    feature["properties"]["marker"] = marker
    feature["properties"]["title"] = title

    if type_name is not None:
        feature["properties"]["ortstyp"] = type_name

    feature["properties"]["hov link"] = hov_link
    feature["properties"]["hov code"] = hov_code

    return feature


def get_hov_data():
    headers = {
        "Authorization": "Bearer " + str(HOV_API_TOKEN),
        "User-Agent": USER_AGENT,
    }
    params = {"fields": ["*", "typ.*"], "limit": -1}

    r = requests.get(HOV_API_BASE_URL, headers=headers, params=params)
    data = r.json()["data"]
    return data


def get_wikidata_image_urls():
    sparql = """
        SELECT ?item ?hovcode ?image_url
        WHERE
        {
        ?item wdt:P7046 ?hovcode.
        ?item wdt:P94 ?image_url.
        }
    """
    headers = {"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT}
    params = {"query": sparql.replace("\n", " ")}

    r = requests.get(WD_BASE_URL, headers=headers, params=params)
    data = r.json()["results"]["bindings"]

    hov_id_image_map = {}

    for record in data:
        image_url = record["image_url"]["value"]

        try:
            hov_code = int(record["hovcode"]["value"])
            hov_id_image_map[hov_code] = image_url
        except ValueError:
            # wikidata entry has no valid hov_code
            continue

    return hov_id_image_map


def generate_geojson():
    hov_image_map = get_wikidata_image_urls()
    hov_data = get_hov_data()

    features = []
    for record in hov_data:
        try:
            image_url = hov_image_map[record["hovcode"]]
            record["image_url"] = image_url
        except KeyError:
            record["image_url"] = None

        try:
            feature = create_feature(record)
        except Exception:
            continue

        features.append(feature)

    print("Collected {nr} features".format(nr=len(features)), file=sys.stderr)
    return {"type": "FeatureCollection", "features": features}


if __name__ == "__main__":
    if HOV_API_TOKEN is None:
        print("HOV_API_TOKEN environment variable is not set.", file=sys.stderr)
        exit(1)

    geojson = generate_geojson()

    print(json.dumps(geojson))

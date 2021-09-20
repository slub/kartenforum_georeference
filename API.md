# API

This file contains a documentation of the API endpoints for the georeference services.

### Statistic 

Endpoint for querying overall statistics regarding the georeference progress / status.

```
GET     /statistics - Returns statistics about the overall georeference progress
```

### User History

Endpoint for querying the georeference progress / work of a individuel user.

```
GET     /user/{user_id}/history - Returns statistics about the overall georeference progress

Example:
curl 'http://localhost:6543/user/user_1/history'
```

### Georeference

Endpoint for querying, validating and confirming georeference processes. A georeference process can be queryied via `map_id` and `georeference_id`. If the `georeference_id` is missing, it returns the current active process for the map object and if one is missing
 it returns an empty process.

```
GET     /maps/{map_id}/georefs 

Example:
curl 'http://localhost:6543/maps/10003265/georefs'  (Empty process)
curl 'http://localhost:6543/maps/10001963/georefs'  (Current active process)

GET     /maps/{map_id}/georefs/{georef_id}

Example:
curl 'http://localhost:6543/maps/10001963/georefs/12347'
```

A specially endpoint allows the generation of validation results. The validation results can be access via a WMS service.

```
POST    /maps/{map_id}/georefs_validate
    With:
        {
            'source': 'pixel', // always has to be "pixel" 
            'target': 'EPSG:4314', // has to be a epsg code
            'algorithm': 'tps', // 'tps', 'affine' or 'polynom' are supported
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]}, // list of gcps
                       {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}]
        }

Example:
curl -XPOST 'http://localhost:6543/maps/10001556/georefs_validate' -H 'Content-Type: application/json' -d '{ "source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]}, {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}]}'
```

The result contains a link on a wms. The wms can be tested via:

> http://localhost:8080/?map=/etc/mapserver/wms_2e93cade-db49-4bc1-909e-1b71b8fe030c.map&Request=GetCapabilities&Service=WMS

Finally a valid georeference process can be confirmed via the following endpoint.

```
POST    /maps/{map_id}/georefs
    With:
        {
          'clip_polygon': {
            'type': 'Polygon',
            'crs': {'type': 'name', 'properties': {'name': 'EPSG:4314'}},
            'coordinates': [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974], [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091], [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772], [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
        },
        'georef_params': {
            'source': 'pixel',
            'target': 'EPSG:4314',
            'algorithm': 'tps',
            'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]}, {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]}, {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}, {'source': [6969, 3160], 'target': [14.816612768409, 50.863606051111]}, {'source': [1907, 1301], 'target': [14.690521818997, 50.891860483128]}, {'source': [4180, 4396], 'target': [14.747856876595, 50.843955582846]}, {'source': [5070, 5489], 'target': [14.769772087663, 50.827125251053]}, {'source': [6933, 7171], 'target': [14.816342007402, 50.801483295161]}, {'source': [3325, 7152], 'target': [14.727274235239, 50.801026963158]}, {'source': [1509, 6622], 'target': [14.681454720195, 50.808715847718]}]
        },
        'type': 'new',
        'user_id': 'user_1'
        }

Example:
curl -XPOST 'http://localhost:6543/maps/10001556/georefs' -H 'Content-Type: application/json' -d '{"clip_polygon": {
            "type": "Polygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:4314"}},
            "coordinates": [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974], [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091], [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772], [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
        },
        "georef_params": {
            "source": "pixel",
            "target": "EPSG:4314",
            "algorithm": "tps",
            "gcps": [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]}, {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}, {"source": [6969, 3160], "target": [14.816612768409, 50.863606051111]}, {"source": [1907, 1301], "target": [14.690521818997, 50.891860483128]}, {"source": [4180, 4396], "target": [14.747856876595, 50.843955582846]}, {"source": [5070, 5489], "target": [14.769772087663, 50.827125251053]}, {"source": [6933, 7171], "target": [14.816342007402, 50.801483295161]}, {"source": [3325, 7152], "target": [14.727274235239, 50.801026963158]}, {"source": [1509, 6622], "target": [14.681454720195, 50.808715847718]}]
        },
        "type": "update",
        "user_id": "user_1"}'
```
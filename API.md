# API

This file contains a documentation of the API endpoints for the georeference services.

## Overview

### API Endpoint

```
http://{host:port}/{route_prefix}
```

The `route_prefix` can be configured within the `georeference/settings.py`. The default value is `''`.

### Statistics and User History

``` 
GET     /statistics - Returns statistics about the managed georeference data and crowd sourcing process
GET     /user/{user_id}/history - Returns data about the georeference history of the user
```

### Georeference 

``` 
GET     /maps/{map_id}/transformations - Returns transformations for a given original map id
POST    /maps/{map_id}/transformations - Create a new transformations for a given original map id
POST    /maps/{map_id}/transformations/try - Produces a temporary georefernence results for a given transformation
```

### Admin

``` 
GET     /admin/georefs?map_id={map_id} - Get all georeference process for a specific map_id
GET     /admin/georefs?user_id={user_id} - Get all georeference process for a specific user_id
GET     /admin/georefs?validation={validation} - Get all georeference process for a specific validation value (isvalide|invalide)
GET     /admin/georefs?pending=true - Get all georeference process which are missing a validation
POST    /admin/georefs/{georef_id} - Set validation to "invalide" or "isvalide"
```

## Statistics and User History

Endpoints for querying overall statistics and specific data associated with the user.

#### GET statistics

HTTP Request:

``` 
GET     /statistics
```

HTTP Response:

``` 
{
   "georeference_points":[
      {
         "userid":"user_1",
         "points":300,
         "new":3,
         "update":12
      },
      {
         "userid":"user_2",
         "points":80,
         "new":4,
         "update":0
      }
   ],
   "georeference_map_count":8,
   "not_georeference_map_count":1
}
```

Curl Example:

``` 
curl -XGET 'http://localhost:6543/statistics' -H 'Content-Type: application/json'
```

Endpoint for querying overall statistics regarding the georeference progress / status.

```
GET     /statistics - Returns statistics about the overall georeference progress
```

#### GET user history

HTTP Request:

``` 
GET     /user/{user_id}/history
```

HTTP Response:

``` 
{
   "georef_profile":[
      {
         "georefid":14624,
         "mapid":"oai:de:slub-dresden:vk:id-10009466",
         "georefparams":{ ... },
         "time":"1855-01-01 00:00:00",
         "transformed":true,
         "isvalide":"",
         "title":"Sect. 09: Dresden",
         "key":"df_dk_0000006",
         "georeftime":"2021-07-05 12:08:44",
         "type":"update",
         "published":true,
         "thumbnail":"http://fotothek.slub-dresden.de/mids/df/dk/0000000/df_dk_0000006.jpg",
         "boundingbox":"13.66397999235858,51.01775115900975,13.800438727264797,51.104439739321236"
      }
   ],
   "points":300
}
```

Curl Example:

``` 
curl -XGET 'http://localhost:6543/user/user_1/history' -H 'Content-Type: application/json'
```

## Georeference

#### GET georeference processes for map id

HTTP Request:

``` 
GET     /maps/{map_id}/georefs
```

HTTP Response:

``` 
# If there exists no georeference process
{
   "extent":null,
   "default_srs":"EPSG:4314",
   "items":[
      
   ],
   "pending_processes":false,
   "enabled_georeference_id":null
}
``` 

``` 
# If there exists a georeference process
{
   "extent":[
      14.6598260493127,
      50.78928846345504,
      14.827457411564726,
      50.898979953060184
   ],
   "default_srs":"EPSG:4314",
   "items":[
      {
         "clip_polygon":{
            "type":"Polygon",
            "crs":{
               "type":"name",
               "properties":{
                  "name":"EPSG:4314"
               }
            },
            "coordinates":[ ... ]
         },
         "params":{
            "source":"pixel",
            "target":"EPSG:4314",
            "algorithm":"tps",
            "gcps":[ ... ]
         },
         "id":11823,
         "timestamp":"2018-02-22 19:21:33",
         "type":"new"
      }
   ],
   "pending_processes":false,
   "enabled_georeference_id":11823
}
``` 

Curl Example:

``` 
curl -XGET 'http://localhost:6543/maps/10001556/georefs' -H 'Content-Type: application/json'
```

#### POST new georeference processes for map id

HTTP Request:

``` 
POST     /maps/{map_id}/georefs
```
``` 
{
   "clip_polygon":{
      "type":"Polygon",
      "crs":{
         "type":"name",
         "properties":{
            "name":"EPSG:4314"
         }
      },
      "coordinates":[
         [
            [
               14.66364715,
               50.899831877
            ],
            ...
         ]
      ]
   },
   "georef_params":{
      "source":"pixel",
      "target":"EPSG:4314",
      "algorithm":"tps",
      "gcps":[
         {
            "source":[
               6700,
               998
            ],
            "target":[
               14.809598142072,
               50.897193140898
            ]
         },
         ...
      ]
   },
   "type":"new",
   "user_id":"test"
}
```

The parameter `type` can have the values `new` or `update`. If there is already a georeference process registered for a map, the API 
will return a HTTP Forbidden in case of the usage of value `new`.

HTTP Response:

``` 
{
   "id":100000,
   "points":20
}
``` 

#### GET georeference process for map id and georeference id

HTTP Request:

``` 
GET     /maps/{map_id}/georefs/{georef_id}
```

HTTP Response:

``` 
{
   "clip_polygon":{
      "type":"Polygon",
      "crs":{
         "type":"name",
         "properties":{
            "name":"EPSG:4314"
         }
      },
      "coordinates":[
         [
            [
               14.66364715,
               50.899831877
            ],
            ...
         ]
      ]
   },
   "georef_params":{
      "source":"pixel",
      "target":"EPSG:4314",
      "algorithm":"tps",
      "gcps":[
         {
            "source":[
               6700,
               998
            ],
            "target":[
               14.809598142072,
               50.897193140898
            ]
         },
        ...
      ]
   },
   "id":11823,
   "timestamp":"2018-02-23 11:17:53",
   "type":"update"
}
``` 

Curl Example:

``` 
curl -XGET 'http://localhost:6543/maps/10001556/georefs/11823' -H 'Content-Type: application/json'
```

#### POST create temporary georeference result

HTTP Request:

``` 
POST    /maps/{map_id}/georefs_validate
```

```
{
   "source":"pixel",
   "target":"EPSG:4314",
   "algorithm":"tps",
   "gcps":[
      {
         "source":[
            6700,
            998
         ],
         "target":[
            14.809598142072,
            50.897193140898
         ]
      },
      {
         "source":[
            6656,
            944
         ],
         "target":[
            14.808447338463,
            50.898010359738
         ]
      },
      {
         "source":[
            6687,
            1160
         ],
         "target":[
            14.809553411787,
            50.894672081543
         ]
      },
      {
         "source":[
            6687,
            1160
         ],
         "target":[
            14.809553411787,
            50.894672081543
         ]
      }
   ]
}
```

HTTP Response:

```
{
   "extent":[
      14.646350123732788,
      50.765199344745504,
      14.860744078415085,
      50.91342767136707
   ],
   "layer_name":"df_dk_0010001_5154_1892",
   "wms_url":"http://localhost:8080/?map=/etc/mapserver/wms_bedea5a9-a883-4bd3-9411-75a1b3267c63.map"
}
```

Curl Example: 

``` 
curl -XPOST 'http://localhost:6543/maps/10001556/georefs_validate' -H 'Content-Type: application/json' -d '{ "source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]}, {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}]}'
```
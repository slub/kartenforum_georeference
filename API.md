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

### Maps

``` 
GET     /maps/{map_id} - Returns basic metadata for a given map id
```

### Transformations

``` 
GET     /transformations/maps/{map_id}  - Get all transformations for a specific map_id
POST    /transformations/maps/{map_id}  - Create a new transformation for a given original map id
GET     /transformations/users/{user_id} - Get all transformations for a specific user_id
GET     /transformations/validations/{missing|valid|invalid} - Get all transformations for a specific validation value
POST    /transformations/try - Produces a temporary georefernence results for a given transformation
```

### Jobs

```
GET     /jobs?pending={true|false}&limit={int} - Get list of jobs
POST    /jobs - Create a new job
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

## Jobs

Endpoint for querying and creating jobs. A job is a task, which is executed by the _daemon_ in an
asynchronous manner. Currently the georeference service supportes three different kinds of jobs:

 <table>
    <tbody>
        <tr>
            <th align="left">Task name</th>
            <th align="left">Task</th>
            <th align="left">Description</th>
        </tr>
        <tr>
            <td align="">transformation_process/td>
            <td align="">
                GeoJSON with parameter:<br /><br />
                <ul>
                    <li><code>transformation_id</code>: Number of a transformation process which should be processed. (Mandatory)</li>
                    <li><code>comment</code>: Comment (Optional)</li>
                </ul>
                <br />
                Example:<br /><br />
                <code>
                    { "transformation_id": 123 }
                </code>
            </td>
            <td align="">Is set by the service api, if a new transformation is created. This task signals the _daemon_ that a new transformation is available and should be processed. 
            </td>
        </tr>
        <tr>
            <td align="">transformation_set_invalid/td>
            <td align="">
                GeoJSON with parameter:<br /><br />
                <ul>
                    <li><code>transformation_id</code>: Number of a transformation process which should be marked as invalid. (Mandatory)</li>
                    <li><code>comment</code>: Comment (Optional)</li>
                </ul>
                <br />
                Example:<br /><br />
                <code>
                    { "transformation_id": 123 }
                </code>
            </td>
            <td align="">This task can be set via the jobs api. It signals that a transformation process should be set as invalid. If the transformation is currently in used by a <code>GeorefMap</code> it is disabled. If there is an older valid transformation for the <code>OriginalMap</code> it is activated or the <code>OriginalMap</code> will be marked as not georeferenced.</td>
        </tr>
    </tbody>
 </table>

#### GET jobs

The GET Endpoint offers two query parameters. `limit` allows the restrict the response count of jobs. The default `limit` is 100. `pending` signals that only pending jobs should be returned.

HTTP Request:

```
GET     /jobs?pending={true|false}&limit={int} - Get list of jobs
```

HTTP Response:

```
[
    {
        "id": 1,
        "processed": true,
        "task": {
            "transformation_id": 2,
        },
        "task_name": "transformation_set_invalid",
        "user_id": "test_user",
        "submitted": "2021-10-01T00:00:00.000"
    }
]
```

Curl Example:

``` 
curl -XGET 'http://localhost:6543/jobs?pending=true' -H 'Content-Type: application/json'
```

#### POST job

TODO



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
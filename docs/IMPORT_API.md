# Import API

## Endpoints

All the endpoints described work asynchronously, which means that input is accepted and checked for validity, and then jobs are created for the actual processing.

In very rare cases, this can lead to changes being accepted but not taking effect until later or, in the case of incorrect processing, not taking effect at all. Particularly when deleting cards, appropriate precautions have been taken to ensure that all possible information is removed even in the event of a partial failure, enabling any remaining files to be removed in subsequent stages.

### POST Map

`POST /maps/ - (Create new Map)`

The request has to be made with the content type `multipart/form-data`.
The two form fields `metadata` and `file` have to be sent with the request.
Metadata has to contain a json string with the following fields:

**Required fields are marked with \*.**

| field_name            | type / values                                    | description                                                                                   |
|-----------------------|--------------------------------------------------|-----------------------------------------------------------------------------------------------|
| allow_download        | boolean                                          | Determines if the raw map file can be downloaded.                                             |
| default_crs           | integer                                          | Integer which represents the EPSG code, which will be used as default value for calculations. |
| * description         | string                                           | Description of the map.                                                                       |
| * license             | string                                           | License of the map.                                                                           |
| link_zoomify          | https-url / (string)                             | Link to the zoomify tile description. Will be generated if left empty.                        |
| link_thumb_small      | https-url / (string)                             | Link to a small thumbnail representation. Will be generated if left empty.                    |
| link_thumb_mid        | https-url / (string)                             | Link to a mid thumbnail representation. Will be generated if left empty.                      |
| * map_scale           | number                                           | Scale of the map, e.g. a scale of 1:25000 = 25000                                             |
| * map_type            | "ae", "ak", "cm", "gl", "mb", "mtb", "tk", "tkx" | Type of the map.                                                                              |
| measures              | string                                           | Measures of the original map, e.g. 48 x 45 cm                                                 |
| * owner               | string                                           | Owner of the original map, e.g. SLUB                                                          |
| permalink             | string                                           | Permalink to the map.                                                                         |
| ppn                   | string                                           | PPN number, e.g. ppn33592090X                                                                 |
| technic               | string                                           | Technic used to produce the original image, e.g. Lithografie & Umdruck                        |
| * time_of_publication | datetime / date                                  | Time at which the original map was publicated either as datetime or iso string.               |
| * title               | string                                           | Title of the map, e.g. "Äquidistantenkarte 107 : Section Zittau, 1892"                        |
| title_series          | string                                           | Title of the map series, e.g. Topographische Karte (Äquidistantenkarte) Sachsen; 5154,1892    |
| * title_short         | string                                           | Short Title of the map, e.g. Section Zittau                                                   |
| type                  | string                                           | Type of the map e.g. Druckgraphic                                                             |

The `file` form field has to contain a valid `.tif` file.

The response contains the map_id with which the map will be created:

```JSON
{
  "map_id": "map_id"
}
```

`POST /maps/{map_id} - (Update existing Map)`

The request has to be made with the content type `multipart/form-data`.
Either a `metadata` or a `file` form field have to be sent with the request.
For the content descriptions of the form fields have a look at the previous sections, with the adjustment that there are no required form fields. The contents of the new metadata from the form field will be merged with the present metadata and will be checked against the described schema. 

In case previously there were external links (thumbnail, zoomify) set, they can be switched to generated links, by setting them to null.

The response contains the map_id of the updated map will be created:

```JSON
{
  "map_id": "map_id"
}
```

### Delete Map

`DELETE /maps/{map_id} - (Delete existing Map)`

Deletes the map with the supplied map_id in case it is available.

The response contains the map_id of the map which will be deleted:

```JSON
{
  "map_id": "map_id"
}
```
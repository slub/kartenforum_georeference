# Scripts

The following sections describe how to use the scripts that are present in this directory.

## data-upload.sh

`./data-upload.sh (create|delete|update) [-f path/to/image/file] [-m path/to/metadata/file] [-b username:password] https://geo.test.kartenforum.slub-dresden.de/maps/?user_id=example_user`

The script allows to use the import api from the command line.

It supports creating, deleting and updating existing maps. The behavior is changed based on the first parameter.

### Create - Explanation of the individual parameters

- (required) create - tells the script it should create a new map
- (required) f - path to the .tif file which should be uploaded
- (required) m - path to the .json file which should be uploaded
- (optional) b - basic auth credentials
- (required) upload-url, without map_id - url to the georef service endpoints

### Upade - Explanation of the individual parameters

"*" - At least one has to be passed - either a new image or new metadata.

- (required) create - tells the script it should create a new map
- (optional*) f - path to the .tif file which should be uploaded
- (optional*) m - path to the .json file which should be uploaded
- (optional) b - basic auth credentials
- (required) upload-url, with map_id - url to the georef service endpoints

### Delete - Explanation of the individual parameters

- (required) create - tells the script it should create a new map
- (optional) b - basic auth credentials
- (required) upload-url, with map_id - url to the georef service endpoints


## batch-upload.sh

`./data-upload.sh [-f] [-b username:password] https://geo.test.kartenforum.slub-dresden.de/maps/?user_id=example_user path/to/upload/directory`

The script allows for creation of new maps in batches. For this, the metadata must be available as a .json file and the corresponding image as a .tif file with the same name in the selected folder (e.g. map_a.json, map_a.tif). 

The paths of the uploaded files and the ids of the associated maps are written to the uploaded.log file. When the script is run again, it checks before uploading a file whether it has already been noted as successfully uploaded in the log. This is checked by the file path.

### Explanation of the individual parameters

- (optional) f - allows to force the upload of already uploaded files
- (optional) b - allows to pass basic-auth credentials to the request
- (required) upload-url - url to the georef service endpoints
- (required) upload-directory - which directory to scan recursively for files to upload


## initialize_zoomify_and_thumbnail.sh

`/initialize_zoomify_and_thumbnail.sh`

The  script is a utility tool designed to initialize thumbnails and zoomify tiles for test data. It automates the process of running python scripts responsible for these initializations within a specified virtual environment.

## download-testdata.sh

`./download-testdata.sh`

The scripts is a utility tool designed to download test data for local development.

## initialize-testdata.sh

`./initialize-testdata.sh`

The scripts is a utility tool designed to initialize test data for local development. It downloads all test data and creates locally thumbnails and zoomify tiles for the test data.


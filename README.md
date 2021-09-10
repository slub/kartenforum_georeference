# Kartenforum Georeference

This repository contains the code for deploying a georeference service as well as a daemon for an asynchrone permanent update of the georeference data basis.

## Install

The georeference service relies on the following dependencies:

```
apt-get install python3 python3-virtualenv libpq-dev gdal-bin libgdal-dev
```

First of all the python dependencies have to be installed. This done by creating a virtual environment:

```
virtualenv python_env

# Install test dependencies
./python_env/bin/pip install -e ".[testing]"

# For setting up a development environment
./python_env/bin/python setup.py develop

# @TODO
# For setting up a production environment
# ./python_env/bin/python setup.py install
```

## Testing

The kartenforum_georeference application uses [pytest](https://docs.pytest.org/en/6.2.x/) as a Test-Runner. For performing a full test run, perform the following command.

```
./python_env/bin/pytest --cov --cov-report=term-missing
```

Make sure that the project is properly installed beforehand.

## API documentation

### ROUTE_PREFIX

```
/georeference
```

The `ROUTE_PREFIX` can be configured within the `georeference/settings.py`. 

### Georeference

```
GET     /georeference/process?mapId={id_of_the_mapobject}|georeferenceId={id_of_the_georeference_process} - Returns a new or the latest georeference process for a map object
POST    /georeference/process/validate - Returns a temporary georeference result for a given set of georeference parameters
POST    /georeference/process/confirm - Persists the parameters of a georeference process.
```

### Statistic 

```
GET     /georeference/statistics - Returns statistics about the overall georeference progress
```

### User

```
GET     /georeference/user/{userId}/history - Returns statistics about the specific user georeference history
```

### Admin

```
GET     /georeference/admin/process?mapid={id_of_the_mapobject}&userid={id_of_the_user}&validation={}
GET     /georeference/admin/setinvalide?georeferenceid={id_of_the_georeference_process}
GET     /georeference/admin/setisvalide?georeferenceid={id_of_the_georeference_process}
```


## Troubleshooting

* If the execution of the command `./python_env/bin/python setup.py develop` fails, make sure that the system wide gdal version, matches the GDAL version within the `setup.py`. 
# kartenforum_georeference

The repository contains the python code for the georeference service and jobs runner of the [Virtual Map Forum 2.0](https://kartenforum.slub-dresden.de/). 

## Purpose

While the [Virtual Map Forum 2.0](https://kartenforum.slub-dresden.de/) is a spatial data infrastructure for searching, visualizing, using and georeferencing rectified historic maps, this repository contains only the backend code for georeferencing historic maps and generate the corresponding backend service. 

Beside that the [Virtual Map Forum 2.0](https://kartenforum.slub-dresden.de/) also includes own basemap and placesearch services as well as a [TYPO3](https://typo3.org/) based web application.

For a deeper dive into this components, have a look at the following repositories:

* [ddev-kartenforum](https://github.com/slub/ddev-kartenforum)
* [slub_web_kartenforum](https://github.com/slub/slub_web_kartenforum)
* [kartenforum_ansible](https://github.com/slub/kartenforum_ansible)

## Documentation

More information regarding this repository can be found within the [docs section](./docs/README.md)

## Install

> Make sure to properly configure the `georeference/settings.py` and the `production.ini`.
>
```
# The application needs this system wide dependencies. 
apt-get install python3 python3-virtualenv libpq-dev gdal-bin libgdal-dev gcc uwsgi libvips-tools

# It is recommended to use a virtualenv for developing
virtualenv python_env
python_env/bin/python setup.py develop
./python_env/bin/pip install -e ".[testing]" --no-cache

# Spawns a georeference service
./python_env/bin/pserve production.ini

# Starts the job runner
python_env/bin/python georeference/daemon/runner.py
```

## Development

>#### Prerequisite
>
> For local development and testing of the project a few further steps have to be executed. First download the `test_data.tar.xz` unpack it and place the image within the directory `./tmp/org_new/`. The password for the SFTP-Service is `8C2Kdpxc2lpUoYBX`.
>
>```
># Download images for running the proper tests
>scp u279620-sub2@u279620-sub2.your-storagebox.de:/test_data_flat.tar.xz ./
>tar -xf test_data_flat.tar.xz -C ./georeference/__test_data/data_input
>```

Because the Georeference Service as well as the Jobs Runner expect different service to interact with, docker can be used to setup a development infrastructure (PostgreSQL Database, Mapserver, Elasticsearch):

``` 
cd docker/
docker-compose up

# To check if the local development environment is setup properly run the following command
./python_env/bin/pytest --cov --cov-report=term-missing

# Starts the test service. Before make sure to properly configure the `georeference/settings.py`
./python_env/bin/pserve development.ini
```
	
## Troubleshooting

* If the execution of the command `./python_env/bin/python setup.py develop` fails, make sure that the system wide gdal version, matches the GDAL version within the `setup.py`. 

* If the execution of the command `./python_env/bin/python setup.py develop` fails with "Unknown distribution option: 'use_2to3_fixers'", install an older version of the setup tools in your virtualenv (<58).



# Kartenforum Georeference

This repository contains the code for deploying a georeference service as well as a daemon for an asynchrone permanent update of the georeference data basis.

## Install

The tools are developed with Python 3.97. They rely on the following dependencies:

```
apt-get install python3 python3-virtualenv libpq-dev gdal-bin libgdal-dev gcc uwsgi
```

The python dependencies are installed within a virtual environment. Therefor run the following commands:

```
virtualenv python_env
./python_env/bin/pip install -e ".[testing]"
```

## Testing & Development

For local development and testing of the project a few further steps have to be executed. First download the `test_data.tar.xz` unpack it and place the image within the directory `./tmp/org_new/`. The password for the SFTP-Service is `8C2Kdpxc2lpUoYBX`.

```
# Download the images
scp u279620-sub2@u279620-sub2.your-storagebox.de:/test_data.tar.xz ./
tar -xf test_data.tar.xz -C ./tmp/org_new/
```

As next step start the docker services (PostgreSQL Database, Mapserver, Elasticsearch):

``` 
cd docker/
docker-compose up
```

Now it should be possible to run all tests of the kartenforum_georeference application. As a test runner [pytest](https://docs.pytest.org/en/6.2.x/) is used. For performing a full test run, perform the following command. 

```
./python_env/bin/pytest --cov --cov-report=term-missing
```

Develop or production services can be started via `pserve`:

```
./python_env/bin/pserve development.ini
./python_env/bin/pserve production.ini
```

Make sure to update the `georeference/settings.py` to your local development environment.

## Processing- & Service-Engine (Daemon)

The Processing- & Service-Engine is a daemon, which runs in the background and performs persistent updates of the search-index and the mapping data. It checks if something has changed
within the database and sync the other services with this update.

The settings for the daemon could be found in the:

```
georeference/settings.py
```

The daemon can be controlled with the following commands:

```
# Starts the daemon
python_env/bin/python georeference/daemon/runner.py
```

#### Find and kill daemons

```
top -c -p $(pgrep -d',' -f python_env)
kill -9
```
	
## Troubleshooting

* If the execution of the command `./python_env/bin/python setup.py develop` fails, make sure that the system wide gdal version, matches the GDAL version within the `setup.py`. 


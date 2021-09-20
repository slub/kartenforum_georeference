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
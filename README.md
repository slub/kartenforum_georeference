# Kartenforum Georeference

This repository contains the code for deploying a georeference service as well as a daemon for an asynchrone permanent 
update of the georeference data basis.

## Install

The georeference service relies on the following dependencies:

```
apt-get install python3 python3-virtualenv libpq-dev
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
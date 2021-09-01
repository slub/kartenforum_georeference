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
virtualenv _python_env

# For setting up a development environment
./_python_env/bin/python setup.py develop

# @TODO
# For setting up a production environment
# ./_python_env/bin/python setup.py install
```
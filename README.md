# kartenforum_georeference

The repository contains the python code for the georeference service of
the [Virtual Map Forum 2.0](https://kartenforum.slub-dresden.de/).

## Get started

### With docker

1. Set up environment for the docker build
    1. There are two environment variables required for the docker build: `USERNAME` and `UID`
    2. `USER=$(whoami)`
    3. `UID=$(id -u)`
    4. Also see this script https://github.com/pikobytes/slub_ddev_kartenforum/blob/main/generate-env.sh for more
       information.
2. `cd docker/`
3. docker-compose up
4. In your IDE make sure to use the correct python interpreter. The one in the `.venv` folder, which should have
   been automatically added by the docker container.
5. The server should be available under `http://localhost:8000/`

### Without Docker

1. Setup poetry according to https://python-poetry.org/docs/
2. Install the required dependencies
    1. `poetry install`
    2. If you experience any issues with python-gdal, make sure the version matches your local gdal version.
3. Set up the pre-commit hooks
    1. `poetry run pre-commit install`

### Configuration

The configuration is done via environment variables.
Environment variables can be set either:

1) Directly in the environment, these will take precedence over everything else
2) In a `.env.production` file in the root of the project. This file will be automatically loaded by `pydantic-settings`
   and will take precedence over the default values defined in `.env`. It does not need to be exhaustive, only the
   variables that should be overwritten are required.
3) In a `.env` file in the root of the project. This file will be automatically loaded by `pydantic-settings`.
4) In the `/georeference/config/settings.py` file. It is responsible for the loading of the environment variables and
   setting the default values. All configurable values and their respective types can be found in this file.

Also see https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support for more information.

### Linting and Formatting

This project uses [ruff](https://docs.astral.sh/ruff/) for formatting and linting.
It is automatically setup via the pyproject.toml file.
Please configure your IDE to use the ruff formatter and linter.
Additionally, they will be run as precommit hooks.

### Running tests

> If you want to run all tests make sure to have [ddev-kartenforum](https://github.com/slub/ddev-kartenforum) locally setup and running. Also make sure to have `sshpass and `libvips-tools` installed.

For running all tests you need to download the test data. This can be done by running the following scripts:

```bash
scripts/download_testdata.sh
```
please install libvips package to create thumbnails:
```shell
sudo apt install libvips libvips-tools
```
Please be aware, that currently the whole test data is up to 3GB in size. If you want to run all tests, you can use the
following command:

```bash
poetry run python -m pytest
```

To run just the test from a specific file, you can use a command with this structure:

```bash
poetry run python -m pytest -rP georeference/tests/utils/proj_test.py::test_get_crs_from_request_params_use_passed_crs
```

Hint: Make sure to have docker running, as the testcontainers library will start a postgres container for the tests.
Hint: Make sure to have `DEV_MODE` enabled. Else ssl verification, if requesting the typo3 application, might fail.
Hint: Make sure to have a local environment properly setup.

## Postgresql Database

docker can be used to set up a development infrastructure

```
cd docker/
docker-compose up
```

### Migrations

In order to modify the database schema, the `alembic` library is used.
It allows for versioned migrations.
The database connection url is read via the `settings.py` file, which reads the `.env` file.

To create a new migration, run the following command:

```
poetry run alembic revision -m "your message"
```

This will create a new migration file in the `alembic/versions` folder.
After you have made your changes, run the following command to apply the migration:

```
poetry run alembic upgrade head
```

For more information also check the [alembic documentation](https://alembic.sqlalchemy.org/en/latest/index.html).

## start

```
uvicorn app.api.server:app --reload
```

## Testing with Postgres-TestContainer and Pytest

In the project's testing process, we use pytest along with
the [postgres-test-container](https://github.com/testcontainers/testcontainers-python) library. Here's how it works:

- **Container Setup:** For each test, we create a temporary Docker container that runs a PostgreSQL database named "
  vkdb" This container sets up the necessary database schema when it's created.

- **Data Initialization:** Before running each test, we make sure to clear any existing datas in tables and
  relationships in the
  database. Then, we populate these tables with initial data to ensure a consistent starting point for testing.

- **Data Cleanup:** After each test, we clean up the data in the tables to maintain a clean slate for the next test.

- **Automatic Cleanup:** Once all tests are completed, the Docker container is automatically stopped and deleted to keep
  your
  environment tidy.

## Run the code with your debugger

Because you are running the Uvicorn server directly from your code, you can call your Python program (your FastAPI
application) directly from the debugger.

If you use Pycharm, you can:

Open the "Run" menu.
in Edit/Run/Debug Configurations' dialog top right select edit configuration.

![Screenshot from 2023-09-04 14-24-33](https://github.com/pikobytes/slub_kartenforum_georeference_fastapi/assets/129738734/43b7464d-ca4f-48f9-8c60-46bbb21c7f31)

Select and add the new configuration (in this case fastAPI and pytest for testing )
Select the file to debug (in this case tests folder for testing and select server.py in app/api/server.py for run server
with uvicorn).
It will then start all the tests, stop at your breakpoints, etc.

if you get an error then try to write the absolute path.


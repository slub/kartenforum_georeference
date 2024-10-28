<h1 align="center">
	<img width="400" alt="The Lounge" src="docs/_assets/header-logo.svg">
</h1>

<h1 align="center">Kartenforum Georeference Service</h1>

<p align="center">
    The <strong>Kartenforum Georeference </strong> provides the georeferencing functionality for the <a href="https://kartenforum.slub-dresden.de/">Virtual Map Forum 2.0</a>.
    This platform allows users to explore and interact with both historical and georeferenced maps. The service is designed to efficiently manage and process georeferenced map data. Using <strong>FastAPI</strong>, it delivers a scalable and high-performance API, while <strong>PostgreSQL</strong> (and PostGIS) manages spatial data storage and queries.
</p>
<br></br> 


## 📖 Table of Contents

- [Get Started](#get-started)
  - [With Docker](#with-docker)
  - [Without Docker](#without-docker)
- [Configuration](#configuration)
- [Linting and Formatting](#linting-and-formatting)
- [Running Tests](#running-tests)
- [PostgreSQL Database](#postgresql-database)
  - [Migrations](#migrations)
- [Testing with Postgres and Testcontainers](#testing-with-postgres-and-testcontainers)
- [Debugging](#debugging)
- [License](#-license)



## Get Started

### With Docker
1. Set environment variables for the docker build: There are two environment variables required for the docker build, `USERNAME` and `UID`
    ```shell
     export USER=$(whoami) 
     export UID=$(id -u)
    ```
    Also see this script https://github.com/pikobytes/slub_ddev_kartenforum/blob/main/generate-env.sh for more
  information.
<br></br>

2. Start Docker containers:

    ```shell
    cd docker/
    docker-compose up
    ```
   
3. In your IDE make sure to use the correct python interpreter. The one in the `.venv` folder, which should have been 
automatically added by the docker container.
<br></br>

4. The server should be available under `http://localhost:8000/`

### Without Docker
1. Set up a virtual environment and install [poetry](https://python-poetry.org/docs/).
    ```shell
    python3 -m venv .venv
    .venv/bin/pip install poetry==1.8.3
    ```

2. Install the required dependencies
    ```shell
    .venv/bin/poetry install
    ```
    In case you experience any issues with python-gdal, make sure the version matches your local gdal version. Also if you
make any changes to `pyproject.toml`. Also, if you make any changes to `pyproject.toml` you need to run `.venv/bin/poetry lock` again.
<br></br>
3. Set Up the pre-commit hooks

    ```shell
    .venv/bin/poetry run pre-commit install
    ```
   
4. Run the server:
    ```shell
    uvicorn app.api.server:app --reload
    ```

## Configuration
Configuration is managed via environment variables. They can be set in the following ways:
1. Directly in the environment: These take precedence over everything else.
2. In a `.env.production` file in the root of the project: This file will be automatically loaded by `pydantic-settings`
   and will take precedence over the default values defined in `.env`. It does not need to be exhaustive, only the
   variables that should be overwritten are required.
3. In a `.env` file: This file is also automatically loaded by `pydantic-settings`.

For more information, check the [Pydantic documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support).


## Linting and Formatting
This project utilizes [ruff](https://docs.astral.sh/ruff/) for both linting and code formatting, with the configuration 
specified in the `pyproject.toml` file. To maintain consistency, please ensure that your IDE is configured to use Ruff for code formatting. Additionally, 
linting and formatting tasks are automatically enforced as pre-commit hooks to help uphold code quality.


## Running Tests
If you want to run all tests make sure to have [ddev-kartenforum](https://github.com/slub/ddev-kartenforum) locally setup and running.
1. Please install the following dependencies and download and initialize the test data:
    
    ```bash
    sudo apt install libvips libvips-tools sshpass libvips-tools
    scripts/initialize-testdata.sh
    ```
2. Run all tests:
    ```shell
    .venv/bin/poetry run pytest 
    ```
3. To run specific tests, use the following command structure:
    ```shell
    .venv/bin/poetry run pytest -rP georeference/tests/utils/proj_test.py::test_get_crs_from_request_params_use_passed_crs
    ```
💡 **Tips:**
* Ensure Docker is running, as the `testcontainers` library will spin up a PostgreSQL container for the tests.
* Make sure `DEV_MODE` is enabled to avoid SSL verification failures when querying the TYPO3 application.
* Properly set up your local environment for testing.


## PostgreSQL Database
docker can be used to set up a development infrastructure

```
cd docker/
docker-compose up
```

### Migrations
To modify the database schema, use the alembic library for versioned migrations. The database connection URL is managed 
in the settings.py file, which reads from the `.env`.

#### Creating a Migration
To create a new migration, run the following command:
  ```shell
   poetry run alembic revision -m "your message"
  ```
This will generate a new migration file in the `alembic/versions` folder.
If the versions folder does not exist inside the alembic directory, please create it manually:
```shell
sudo mkdir alembic/versions
```
#### Applying a Migration
After making your changes, apply the migration using the command:
```
poetry run alembic upgrade head
```
This updates the database schema to the latest version. For more information also check the [alembic documentation](https://alembic.sqlalchemy.org/en/latest/index.html).


## Testing with Postgres and Testcontainers
The project uses [postgres-test-container](https://github.com/testcontainers/testcontainers-python) library.

### How it works:
- **Container Setup:** <br> 
    For each test, a temporary Docker container is created, running a PostgreSQL database called `vkdb`.
    The necessary database schema is automatically set up when the container is initialized.

- **Data Initialization:** <br> 
  Before running each test, we make sure to clear any existing datas in tables and
  relationships in the
  database. Then, we populate these tables with initial data to ensure a consistent starting point for testing.

- **Data Cleanup:** <br> 
  After each test, we clean up the data in the tables to maintain a clean slate for the next test.

- **Automatic Cleanup:** <br> 
  Once all tests are completed, the Docker container is automatically stopped and deleted to keep
  your environment tidy.

## Debugging

To facilitate debugging, you can run the application directly through your IDE’s debugger, allowing you to set breakpoints, inspect variables, and step through the code.

### Debugging with PyCharm

1. **Open the Run/Debug Configurations:**  
   In the top-right corner of PyCharm, click on the dropdown next to the run button and select *Edit Configurations*.

2. **Add a New Configuration:**  
   Create a new configuration for FastAPI or Pytest:
   - For test debugging, select the Pytest option and specify the test files or directories you wish to debug.

3. **Start Debugging:**  
   Once set up, you can start the server or run tests in debug mode. The debugger will pause at any breakpoints you've set, allowing for detailed inspection of the execution flow.

> 💡**Tip:**  
> If you encounter issues with relative paths, try using the absolute path to the files in the configuration.


## 📜 License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) - see the [LICENSE](LICENSE) file for details.



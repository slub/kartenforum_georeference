# Docker

The `docker-compose.yml` contains the specification of a full developer setup for the __Georeferencer Application__. It
contains the following services:

* PostgreSQL 13 with PostGIS 3.1
* pgAdmin4

To start the developer setup run the following command:

> docker-compose up

After that you can access pgAdmin via a Browser and the URL `http://localhost:5050`. The user is `admin@admin.com` with
the password
`postgres`.

For accessing the database `vkdb` via pgAdmin you have to create a connection. Therefor use the following settings:

* Host: pg_container
* Port: 5432
* Username: postgres
* Password: postgres

## Testing of the infrastructure

To setup the full infrastructure. For that, before docker-compose is run, please run the following command within your
root directory.

> docker build -t kartenforum_georeference -f docker/Dockerfile .

As an alternative run

> docker-compose build
>

## Development

When the postgresql docker containers are started, the database creation scripts are mounted.
These are used when starting the development environment, as well as when running the tests.
These can be found in the `/database` directory.

The database creation scripts are executed in the following order:

1. `vkdb-schema.sql` (Create schema)
2. `test-data.sql` (Create test data)
3. `update-sequences.sql` (Update sequences based on test data)

For more information about the used docker images see:

* https://registry.hub.docker.com/_/postgres/
* https://registry.hub.docker.com/r/postgis/postgis/



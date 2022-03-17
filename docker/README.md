# Docker

The `docker-compose.yml` contains the specification of a full developer setup for the __Georeferencer Application__. It
contains the following services:

* PostgreSQL 13 with PostGIS 3.1
* pgAdmin4 

To start the developer setup run the following command:

> docker-compose up

After that you can access pgAdmin via a Browser and the URL `http://localhost:5050`. The user is `admin@admin.com` with the password
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

As part of the deployment of the docker images a database creation script is mounted and executed. It can be found
in the directory `./docker-entrypoint-initdb.d/01-init-db.sh`.

For more information about the used docker images see:

* https://registry.hub.docker.com/_/postgres/
* https://registry.hub.docker.com/r/postgis/postgis/



## Database Migration

The old Virtual Map Forum relies on an older database schema. For usage with the new production setup it has to be updated. This can be done as follows:

1.) Create a new empty database, e.g. vkdb-migration
2.) Create a new empty database which should be the new database, e.g. vkdb-new
3.) Import schemas for both database

  > psql -h localhost -U postgres vkdb-migration < vkdb-migration.sql
  > psql -h localhost -U postgres vkdb-new < vkdb-new.sql

4.) Import old data into the database vkdb-migration

  > psql -h localhost -p 5432 -U postgres vkdb-migration < vkdb-prod.last

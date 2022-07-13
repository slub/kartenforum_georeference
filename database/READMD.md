## Database Migration

The old Virtual Map Forum relies on an older database schema. For usage with the new production setup it has to be updated. This can be done as follows:

1.) Create a new empty database, e.g. vkdb-migration
2.) Create a new empty database which should be the new database, e.g. vkdb-new

3.) Import schemas for both database

  > psql -h localhost -U postgres vkdb-migration < vkdb-migration.sql
  > psql -h localhost -U postgres vkdb-new < vkdb-new.sql

4.) Create dump from current production database

  > pg_dump --inserts --column-inserts -U postgres -h localhost vkdb-prod > vkdb-prod.dump 

5.) Import old data into the database vkdb-migration

  > psql -h localhost -p 5432 -U postgres vkdb-migration < vkdb-prod.dump

5.) Run the migration script

 > python migration.py

6.) Fix sequences via script

 > psql -h localhost -p 5432 -U postgres vkdb-new < vkdb-new_fix-sequences.sql
   
6.) Create dump of migrated database

 > pg_dump --inserts --column-inserts -U postgres -h localhost vkdb-new > vkdb-new.dump

6.) Adjust sequence id of the database

## Scripts

A scripts for updating the map_scale from raw_maps from the current scale field in metadata:

```sql
update raw_maps 
set map_scale = split_part(metadata.scale, ':', 2)::int4
from metadata 
where id = metadata.raw_map_id and split_part(metadata.scale, ':', 2)::int4 > 0;
```

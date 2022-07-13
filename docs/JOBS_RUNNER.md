# Jobs runner

The jobs runner is a python daemon, which runs in the background and checks in a configured time interval for new jobs in the database. If it find new jobs, it processes them. 

## Start & Stop

```
# Starts the daemon
python_env/bin/python georeference/daemon/runner.py

# Find and kill daemons
top -c -p $(pgrep -d',' -f python_env)
kill -9
```

The jobs runner also uses the `georeference/settings.py` and the `production.ini`. Make sure to configure them properly.

## Documentation

The jobs runner makes sure to keep the different geo- and image services from the [Virtual Map Forum](https://kartenforum.slub-dresden.de/) in sync with the current state of the database. To do this, it requests jobs from the jobs table of the `vkdb` at regular intervals and processes them in sequence.

Currently three different kind of jobs are supported:

| job name | description | module| 
|:---|---|---|
| transformation_process | This job takes the references transformation and enable it. Part of enabling a transformation is to create a georeference image based on the transformation, create the corresponding geo services and tms directory and update the index. | ./georeference/jobs/process_transformation.py |
| transformation_set_valid | This job marks a transformation as valid. If this is the first valid and up to date transformation for a given raw maps, a new georef map is created. The process therefore is the same as described for `transformation_process`. | ./georeference/jobs/set_validation.py |
| transformation_set_invalid | This job marks a transformation as invalid. If this transformation is in used it checks if there is prevoius valid transformation and enables this one. If there is no valid transformation if disables all geo services and tms for a map and marks it as not georeferenced. |  ./georeference/jobs/set_validation.py |
| initialze_data | Make sure to initialize produce missing georeference image, geo services and tms directories and creates the index. |  ./georeference/jobs/initialize_data.py |


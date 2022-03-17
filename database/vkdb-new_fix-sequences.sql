SELECT setval('jobs_id_seq', max(id)) FROM jobs;
SELECT setval('original_maps_id_seq', max(id)) FROM original_maps;
SELECT setval('transformations_id_seq', max(id)) FROM transformations;
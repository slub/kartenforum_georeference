SELECT setval('jobs_id_seq', max(id))
FROM jobs;
SELECT setval('raw_maps_id_seq', max(id))
FROM raw_maps;
SELECT setval('transformations_id_seq', max(id))
FROM transformations;
SELECT setval('mosaic_maps_id_seq', max(id))
FROM mosaic_maps;
SELECT setval('map_view_id_seq', max(id))
FROM map_view;

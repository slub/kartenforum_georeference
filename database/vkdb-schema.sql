-- Database: vkdb
--DROP DATABASE vkdb;

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: georef_maps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.georef_maps
(
    raw_map_id        integer                     NOT NULL,
    transformation_id integer                     NOT NULL,
    rel_path          character varying,
    extent            public.geometry,
    last_processed    timestamp without time zone NOT NULL,
    CONSTRAINT enforce_dims_boundingbox CHECK ((public.st_ndims(extent) = 2)),
    CONSTRAINT enforce_geotype_boundingbox CHECK (((public.geometrytype(extent) = 'POLYGON'::text) OR (extent IS NULL))),
    CONSTRAINT enforce_srid_the_extent CHECK ((public.st_srid(extent) = 4326))
);


ALTER TABLE public.georef_maps
    OWNER TO postgres;

--
-- Name: georef_maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.georef_maps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.georef_maps_id_seq
    OWNER TO postgres;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.jobs
(
    id          integer                     NOT NULL,
    type        character varying           NOT NULL,
    description character varying,
    state       character varying           NOT NULL,
    submitted   timestamp without time zone NOT NULL,
    user_id     character varying           NOT NULL,
    comment     character varying DEFAULT ''::character varying,
    CONSTRAINT check_state CHECK (((state)::text = ANY
                                   ((ARRAY ['not_started'::character varying, 'completed'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT check_type CHECK (((type)::text = ANY
                                  ((ARRAY ['transformation_process'::character varying, 'transformation_set_valid'::character varying, 'transformation_set_invalid'::character varying, 'maps_create'::character varying, 'maps_delete'::character varying, 'maps_update'::character varying, 'mosaic_map_create'::character varying, 'mosaic_map_delete'::character varying])::text[])))
);


ALTER TABLE public.jobs
    OWNER TO postgres;

--
-- Name: jobs_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.jobs_history
(
    id          integer                     NOT NULL,
    type        character varying           NOT NULL,
    description character varying,
    state       character varying           NOT NULL,
    submitted   timestamp without time zone NOT NULL,
    user_id     character varying           NOT NULL,
    comment     character varying DEFAULT ''::character varying,
    CONSTRAINT check_state CHECK (((state)::text = ANY
                                   ((ARRAY ['not_started'::character varying, 'completed'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT check_type CHECK (((type)::text = ANY
                                  ((ARRAY ['transformation_process'::character varying, 'transformation_set_valid'::character varying, 'transformation_set_invalid'::character varying, 'maps_create'::character varying, 'maps_delete'::character varying, 'maps_update'::character varying, 'mosaic_map_create'::character varying, 'mosaic_map_delete'::character varying])::text[])))
);


ALTER TABLE public.jobs_history
    OWNER TO postgres;

--
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.jobs_id_seq
    OWNER TO postgres;

--
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.jobs_id_seq OWNED BY public.jobs.id;

--
-- Name: mosaic_maps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mosaic_maps
(
    id                   integer                     NOT NULL,
    name                 character varying           NOT NULL
        CONSTRAINT name_unique UNIQUE,
    raw_map_ids          integer[]                   NOT NULL,
    title                character varying,
    title_short          character varying           NOT NULL,
    description          character varying           NOT NULL,
    time_of_publication  timestamp without time zone NOT NULL,
    link_thumb           character varying           NOT NULL,
    map_scale            integer                     NOT NULL,
    last_change          timestamp without time zone NOT NULL,
    last_service_update  timestamp without time zone,
    last_overview_update timestamp without time zone
);

ALTER TABLE public.mosaic_maps
    OWNER TO postgres;

--
-- Name: mosaic_maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mosaic_maps_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.mosaic_maps_id_seq
    OWNER TO postgres;

--
-- Name: mosaic_maps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mosaic_maps_id_seq OWNED BY public.mosaic_maps.id;

--
-- Name: map_view; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.map_view
(
    id            integer           NOT NULL,
    map_view_json character varying NOT NULL,
    public_id     character varying NOT NULL,
    submitted     timestamp without time zone,
    request_count integer,
    last_request  timestamp without time zone,
    user_id       character varying
);


ALTER TABLE public.map_view
    OWNER TO postgres;

--
-- Name: map_view_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.map_view_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.map_view_id_seq
    OWNER TO postgres;

--
-- Name: map_view_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.map_view_id_seq OWNED BY public.map_view.id;


--
-- Name: metadata; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.metadata
(
    raw_map_id          integer NOT NULL,
    title               character varying,
    title_short         character varying,
    title_serie         character varying,
    description         character varying,
    measures            character varying,
    type                character varying,
    technic             character varying,
    ppn                 character varying,
    permalink           character varying,
    license             character varying,
    owner               character varying,
    link_zoomify        character varying,
    time_of_publication timestamp without time zone,
    link_thumb_small    character varying,
    link_thumb_mid      character varying
);


ALTER TABLE public.metadata
    OWNER TO postgres;

--
-- Name: raw_maps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.raw_maps
(
    id             integer               NOT NULL,
    file_name      character varying,
    enabled        boolean,
    map_type       character varying,
    default_crs    integer,
    rel_path       character varying,
    map_scale      integer,
    allow_download boolean DEFAULT false NOT NULL
);


ALTER TABLE public.raw_maps
    OWNER TO postgres;

--
-- Name: raw_maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.raw_maps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.raw_maps_id_seq
    OWNER TO postgres;

--
-- Name: raw_maps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.raw_maps_id_seq OWNED BY public.raw_maps.id;


--
-- Name: transformations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transformations
(
    id         integer                     NOT NULL,
    submitted  timestamp without time zone NOT NULL,
    user_id    character varying           NOT NULL,
    params     character varying           NOT NULL,
    target_crs integer                     NOT NULL,
    validation character varying           NOT NULL,
    raw_map_id integer                     NOT NULL,
    overwrites integer                     NOT NULL,
    comment    character varying,
    clip       public.geometry,
    CONSTRAINT check_validation CHECK (((validation)::text = ANY
                                        ((ARRAY ['missing'::character varying, 'valid'::character varying, 'invalid'::character varying])::text[]))),
    CONSTRAINT enforce_dims_clip CHECK ((public.st_ndims(clip) = 2)),
    CONSTRAINT enforce_geotype_clip CHECK (((public.geometrytype(clip) = 'POLYGON'::text) OR (clip IS NULL))),
    CONSTRAINT enforce_srid_the_clip CHECK ((public.st_srid(clip) = 4326))
);


ALTER TABLE public.transformations
    OWNER TO postgres;

--
-- Name: transformations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transformations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transformations_id_seq
    OWNER TO postgres;

--
-- Name: transformations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transformations_id_seq OWNED BY public.transformations.id;


--
-- Name: jobs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jobs
    ALTER COLUMN id SET DEFAULT nextval('public.jobs_id_seq'::regclass);


--
-- Name: map_view id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.map_view
    ALTER COLUMN id SET DEFAULT nextval('public.map_view_id_seq'::regclass);


--
-- Name: raw_maps id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.raw_maps
    ALTER COLUMN id SET DEFAULT nextval('public.raw_maps_id_seq'::regclass);


--
-- Name: transformations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transformations
    ALTER COLUMN id SET DEFAULT nextval('public.transformations_id_seq'::regclass);

--
-- Name: georef_maps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.georef_maps_id_seq', 1, false);


--
-- Name: jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.jobs_id_seq', 28, true);


--
-- Name: map_view_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.map_view_id_seq', 1, false);


--
-- Name: raw_maps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.raw_maps_id_seq', 1, false);


--
-- Name: transformations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transformations_id_seq', 42, true);


--
-- Name: georef_maps georef_maps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.georef_maps
    ADD CONSTRAINT georef_maps_pkey PRIMARY KEY (raw_map_id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: map_view map_view_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.map_view
    ADD CONSTRAINT map_view_pk PRIMARY KEY (id);


--
-- Name: map_view map_view_public_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.map_view
    ADD CONSTRAINT map_view_public_id_key UNIQUE (public_id);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (raw_map_id);


--
-- Name: raw_maps raw_maps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.raw_maps
    ADD CONSTRAINT raw_maps_pkey PRIMARY KEY (id);

--
-- Name: mosaic_maps id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mosaic_maps
    ALTER COLUMN id SET DEFAULT nextval('public.mosaic_maps_id_seq'::regclass);

--
-- Name: mosaic_maps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mosaic_maps_id_seq', 1, false);

--
-- Name: transformations transformations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transformations
    ADD CONSTRAINT transformations_pkey PRIMARY KEY (id);


--
-- Name: raw_maps unique_filename; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.raw_maps
    ADD CONSTRAINT unique_filename UNIQUE (file_name);


--
-- Name: fki_transformations_raw_map_id_fkey; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_transformations_raw_map_id_fkey ON public.transformations USING btree (raw_map_id);


--
-- Name: idx_raw_maps_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_raw_maps_id ON public.raw_maps USING btree (id);


--
-- Name: idx_transformations_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_transformations_id ON public.transformations USING btree (id);


--
-- Name: map_view_id_uindex; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX map_view_id_uindex ON public.map_view USING btree (id);


--
-- Name: map_view_public_id_uindex; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX map_view_public_id_uindex ON public.map_view USING btree (public_id);


--
-- Name: georef_maps georef_maps_raw_maps_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.georef_maps
    ADD CONSTRAINT georef_maps_raw_maps_id_fkey FOREIGN KEY (raw_map_id) REFERENCES public.raw_maps (id) ON DELETE CASCADE;


--
-- Name: georef_maps georef_maps_transformations_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.georef_maps
    ADD CONSTRAINT georef_maps_transformations_id_fkey FOREIGN KEY (transformation_id) REFERENCES public.transformations (id);


--
-- Name: metadata metadata_maps_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metadata
    ADD CONSTRAINT metadata_maps_fkey FOREIGN KEY (raw_map_id) REFERENCES public.raw_maps (id) ON DELETE CASCADE;


--
-- Name: transformations transformations_raw_maps_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transformations
    ADD CONSTRAINT transformations_raw_maps_id_fkey FOREIGN KEY (raw_map_id) REFERENCES public.raw_maps (id) ON DELETE CASCADE;



--
-- PostgreSQL database dump complete
--


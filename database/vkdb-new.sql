--
-- PostgreSQL database dump
--

-- Dumped from database version 13.4 (Debian 13.4-4.pgdg110+1)
-- Dumped by pg_dump version 13.4 (Ubuntu 13.4-0ubuntu0.21.04.1)

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

CREATE TABLE public.georef_maps (
    original_map_id integer NOT NULL,
    transformation_id integer NOT NULL,
    rel_path character varying,
    extent public.geometry,
    last_processed timestamp without time zone NOT NULL,
    CONSTRAINT enforce_dims_boundingbox CHECK ((public.st_ndims(extent) = 2)),
    CONSTRAINT enforce_geotype_boundingbox CHECK (((public.geometrytype(extent) = 'POLYGON'::text) OR (extent IS NULL)))
);


ALTER TABLE public.georef_maps OWNER TO postgres;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.jobs (
    id integer NOT NULL,
    submitted timestamp without time zone NOT NULL,
    user_id character varying NOT NULL,
    task character varying,
    task_name character varying NOT NULL,
    comment character varying DEFAULT ''::character varying,
    processed boolean DEFAULT false
);


ALTER TABLE public.jobs OWNER TO postgres;

--
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.jobs_id_seq OWNER TO postgres;

--
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.jobs_id_seq OWNED BY public.jobs.id;


--
-- Name: metadata; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.metadata (
    original_map_id integer NOT NULL,
    title character varying,
    title_short character varying,
    title_serie character varying,
    fotothek_id integer,
    description character varying,
    measures character varying,
    scale character varying,
    type character varying,
    technic character varying,
    ppn character varying,
    license character varying,
    time_of_publication timestamp without time zone,
    owner character varying,
    permalink character varying,
    link_jpg character varying,
    link_zoomify character varying,
    link_thumb_small character varying,
    link_thumb_mid character varying
);


ALTER TABLE public.metadata OWNER TO postgres;

--
-- Name: original_maps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.original_maps (
    id integer NOT NULL,
    file_name character varying,
    rel_path character varying,
    enabled boolean,
    map_type character varying,
    default_srs integer DEFAULT 4326 NOT NULL,
    map_scale integer
);


ALTER TABLE public.original_maps OWNER TO postgres;

--
-- Name: original_maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.original_maps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.original_maps_id_seq OWNER TO postgres;

--
-- Name: original_maps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.original_maps_id_seq OWNED BY public.original_maps.id;


--
-- Name: transformations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transformations (
    id integer NOT NULL,
    original_map_id integer NOT NULL,
    submitted timestamp without time zone NOT NULL,
    user_id character varying NOT NULL,
    params character varying NOT NULL,
    clip public.geometry,
    overwrites integer NOT NULL,
    validation character varying NOT NULL,
    comment character varying,
    CONSTRAINT enforce_dims_clip CHECK ((public.st_ndims(clip) = 2)),
    CONSTRAINT enforce_geotype_clip CHECK (((public.geometrytype(clip) = 'POLYGON'::text) OR (clip IS NULL)))
);


ALTER TABLE public.transformations OWNER TO postgres;

--
-- Name: transformations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transformations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transformations_id_seq OWNER TO postgres;

--
-- Name: transformations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transformations_id_seq OWNED BY public.transformations.id;


--
-- Name: jobs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jobs ALTER COLUMN id SET DEFAULT nextval('public.jobs_id_seq'::regclass);


--
-- Name: original_maps id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.original_maps ALTER COLUMN id SET DEFAULT nextval('public.original_maps_id_seq'::regclass);


--
-- Name: transformations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transformations ALTER COLUMN id SET DEFAULT nextval('public.transformations_id_seq'::regclass);


--
-- Name: georef_maps georef_maps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.georef_maps
    ADD CONSTRAINT georef_maps_pkey PRIMARY KEY (original_map_id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (original_map_id);


--
-- Name: original_maps original_maps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.original_maps
    ADD CONSTRAINT original_maps_pkey PRIMARY KEY (id);


--
-- Name: transformations transformations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transformations
    ADD CONSTRAINT transformations_pkey PRIMARY KEY (id);


--
-- Name: original_maps unique_filename; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.original_maps
    ADD CONSTRAINT unique_filename UNIQUE (file_name);


--
-- Name: fki_transformations_original_map_id_fkey; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_transformations_original_map_id_fkey ON public.transformations USING btree (original_map_id);


--
-- Name: idx_original_maps_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_original_maps_id ON public.original_maps USING btree (id);


--
-- Name: idx_transformations_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_transformations_id ON public.transformations USING btree (id);


--
-- Name: georef_maps georef_maps_original_maps_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.georef_maps
    ADD CONSTRAINT georef_maps_original_maps_id_fkey FOREIGN KEY (original_map_id) REFERENCES public.original_maps(id);


--
-- Name: georef_maps georef_maps_transformations_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.georef_maps
    ADD CONSTRAINT georef_maps_transformations_id_fkey FOREIGN KEY (transformation_id) REFERENCES public.transformations(id);


--
-- Name: metadata metadata_maps_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metadata
    ADD CONSTRAINT metadata_maps_fkey FOREIGN KEY (original_map_id) REFERENCES public.original_maps(id);


--
-- Name: transformations transformations_original_maps_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transformations
    ADD CONSTRAINT transformations_original_maps_id_fkey FOREIGN KEY (original_map_id) REFERENCES public.original_maps(id);


--
-- PostgreSQL database dump complete
--



--
-- New map_view table
--
CREATE TABLE map_view
(
    id            serial
        CONSTRAINT map_view_pk
            PRIMARY KEY,
    map_view_json character varying NOT NULL,
    public_id character varying UNIQUE NOT NULL,
    submitted     timestamp,
    request_count integer,
    last_request  timestamp,
    user_id       character varying
);

ALTER TABLE map_view OWNER TO postgres;

CREATE UNIQUE INDEX map_view_id_uindex ON map_view (id);
CREATE UNIQUE INDEX map_view_public_id_uindex ON map_view (public_id);
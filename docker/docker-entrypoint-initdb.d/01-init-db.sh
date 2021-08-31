#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Database: vkdb
    --DROP DATABASE vkdb;

    CREATE DATABASE vkdb
        WITH
        OWNER = postgres
        ENCODING = 'UTF8'
        LC_COLLATE = 'en_US.utf8'
        LC_CTYPE = 'en_US.utf8'
        TABLESPACE = pg_default
        CONNECTION LIMIT = -1;

    -- Connect to database
    \connect vkdb $POSTGRES_USER

    --
    -- PostgreSQL database dump
    --

    -- Dumped from database version 13.3 (Debian 13.3-1.pgdg100+1)
    -- Dumped by pg_dump version 13.3 (Debian 13.3-1.pgdg100+1)

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
    -- Name: adminjobs; Type: TABLE; Schema: public; Owner: postgres
    --

    CREATE TABLE public.adminjobs (
        id integer NOT NULL,
        processed boolean DEFAULT false,
        georefid integer,
        setto character varying,
        "timestamp" timestamp without time zone,
        userid character varying NOT NULL,
        comment character varying DEFAULT ''::character varying
    );


    ALTER TABLE public.adminjobs OWNER TO postgres;

    --
    -- Name: adminjobs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
    --

    CREATE SEQUENCE public.adminjobs_id_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;


    ALTER TABLE public.adminjobs_id_seq OWNER TO postgres;

    --
    -- Name: adminjobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
    --

    ALTER SEQUENCE public.adminjobs_id_seq OWNED BY public.adminjobs.id;


    --
    -- Name: georeferenzierungsprozess; Type: TABLE; Schema: public; Owner: postgres
    --

    CREATE TABLE public.georeferenzierungsprozess (
        id integer NOT NULL,
        messtischblattid integer,
        clipparameter character varying,
        "timestamp" timestamp without time zone,
        type character varying,
        nutzerid character varying NOT NULL,
        processed boolean DEFAULT false,
        georefparams character varying,
        isactive boolean,
        adminvalidation character varying,
        mapid integer,
        overwrites integer,
        comment character varying,
        clippolygon character varying,
        algorithm character varying
    );


    ALTER TABLE public.georeferenzierungsprozess OWNER TO postgres;

    --
    -- Name: georeferenzierungsprozess_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
    --

    CREATE SEQUENCE public.georeferenzierungsprozess_id_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;


    ALTER TABLE public.georeferenzierungsprozess_id_seq OWNER TO postgres;

    --
    -- Name: georeferenzierungsprozess_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
    --

    ALTER SEQUENCE public.georeferenzierungsprozess_id_seq OWNED BY public.georeferenzierungsprozess.id;


    --
    -- Name: map; Type: TABLE; Schema: public; Owner: postgres
    --

    CREATE TABLE public.map (
        id integer NOT NULL,
        apsobjectid integer,
        apsdateiname character varying,
        originalimage character varying,
        georefimage character varying,
        istaktiv boolean,
        isttransformiert boolean,
        maptype character varying,
        hasgeorefparams integer DEFAULT 0,
        boundingbox public.geometry,
        recommendedsrid integer DEFAULT 4314 NOT NULL,
        CONSTRAINT enforce_dims_boundingbox CHECK ((public.st_ndims(boundingbox) = 2)),
        CONSTRAINT enforce_geotype_boundingbox CHECK (((public.geometrytype(boundingbox) = 'POLYGON'::text) OR (boundingbox IS NULL))),
        CONSTRAINT enforce_srid_boundingbox CHECK ((public.st_srid(boundingbox) = 4314))
    );


    ALTER TABLE public.map OWNER TO postgres;

    --
    -- Name: maps_apsobjectid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
    --

    CREATE SEQUENCE public.maps_apsobjectid_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;


    ALTER TABLE public.maps_apsobjectid_seq OWNER TO postgres;

    --
    -- Name: maps_apsobjectid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
    --

    ALTER SEQUENCE public.maps_apsobjectid_seq OWNED BY public.map.apsobjectid;


    --
    -- Name: maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
    --

    CREATE SEQUENCE public.maps_id_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;


    ALTER TABLE public.maps_id_seq OWNER TO postgres;

    --
    -- Name: maps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
    --

    ALTER SEQUENCE public.maps_id_seq OWNED BY public.map.id;


    --
    -- Name: metadata; Type: TABLE; Schema: public; Owner: postgres
    --

    CREATE TABLE public.metadata (
        mapid integer NOT NULL,
        title character varying,
        titleshort character varying,
        serientitle character varying,
        description character varying,
        measures character varying,
        scale character varying,
        type character varying,
        technic character varying,
        ppn character varying,
        apspermalink character varying,
        imagelicence character varying,
        imageowner character varying,
        imagejpg character varying,
        imagezoomify character varying,
        timepublish timestamp without time zone,
        blattnr character varying,
        thumbssmall character varying,
        thumbsmid character varying
    );


    ALTER TABLE public.metadata OWNER TO postgres;

    --
    -- Name: adminjobs id; Type: DEFAULT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.adminjobs ALTER COLUMN id SET DEFAULT nextval('public.adminjobs_id_seq'::regclass);


    --
    -- Name: georeferenzierungsprozess id; Type: DEFAULT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.georeferenzierungsprozess ALTER COLUMN id SET DEFAULT nextval('public.georeferenzierungsprozess_id_seq'::regclass);


    --
    -- Name: map id; Type: DEFAULT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.map ALTER COLUMN id SET DEFAULT nextval('public.maps_id_seq'::regclass);


    --
    -- Name: map apsobjectid; Type: DEFAULT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.map ALTER COLUMN apsobjectid SET DEFAULT nextval('public.maps_apsobjectid_seq'::regclass);


    --
    -- Name: adminjobs adminjobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.adminjobs
        ADD CONSTRAINT adminjobs_pkey PRIMARY KEY (id);


    --
    -- Name: georeferenzierungsprozess georeferenzierungsprozess_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.georeferenzierungsprozess
        ADD CONSTRAINT georeferenzierungsprozess_pkey PRIMARY KEY (id);


    --
    -- Name: map maps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.map
        ADD CONSTRAINT maps_pkey PRIMARY KEY (id);


    --
    -- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.metadata
        ADD CONSTRAINT metadata_pkey PRIMARY KEY (mapid);


    --
    -- Name: map unique_apsdateiname; Type: CONSTRAINT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.map
        ADD CONSTRAINT unique_apsdateiname UNIQUE (apsdateiname);


    --
    -- Name: fki_georeferenzierungsprozess_maps_fkey; Type: INDEX; Schema: public; Owner: postgres
    --

    CREATE INDEX fki_georeferenzierungsprozess_maps_fkey ON public.georeferenzierungsprozess USING btree (mapid);


    --
    -- Name: idx_georeferenzierungsprozess_id; Type: INDEX; Schema: public; Owner: postgres
    --

    CREATE UNIQUE INDEX idx_georeferenzierungsprozess_id ON public.georeferenzierungsprozess USING btree (id);


    --
    -- Name: idx_maps_id; Type: INDEX; Schema: public; Owner: postgres
    --

    CREATE UNIQUE INDEX idx_maps_id ON public.map USING btree (id);


    --
    -- Name: isactive_idx; Type: INDEX; Schema: public; Owner: postgres
    --

    CREATE UNIQUE INDEX isactive_idx ON public.georeferenzierungsprozess USING btree (mapid) WHERE (isactive = true);


    --
    -- Name: maps_boundingbox_gist; Type: INDEX; Schema: public; Owner: postgres
    --

    CREATE INDEX maps_boundingbox_gist ON public.map USING gist (boundingbox);

    ALTER TABLE public.map CLUSTER ON maps_boundingbox_gist;


    --
    -- Name: adminjobs adminjobs_georeferenzierungsprozess_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.adminjobs
        ADD CONSTRAINT adminjobs_georeferenzierungsprozess_fkey FOREIGN KEY (georefid) REFERENCES public.georeferenzierungsprozess(id);


    --
    -- Name: metadata metadata_maps_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
    --

    ALTER TABLE ONLY public.metadata
        ADD CONSTRAINT metadata_maps_fkey FOREIGN KEY (mapid) REFERENCES public.map(id);


    --
    -- PostgreSQL database dump complete
    --
EOSQL
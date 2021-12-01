#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Database: vkdb_test
    --DROP DATABASE vkdb_test;

    CREATE DATABASE vkdb_test
        WITH
        OWNER = postgres
        ENCODING = 'UTF8'
        LC_COLLATE = 'en_US.utf8'
        LC_CTYPE = 'en_US.utf8'
        TABLESPACE = pg_default
        CONNECTION LIMIT = -1;

    -- Connect to database
    \connect vkdb_test $POSTGRES_USER

    --
    -- PostgreSQL database dump
    --

    -- Dumped from database version 13.4 (Debian 13.4-4.pgdg110+1)
    -- Dumped by pg_dump version 13.5 (Ubuntu 13.5-0ubuntu0.21.04.1)

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
    -- Name: georef_maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
    --

    CREATE SEQUENCE public.georef_maps_id_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;


    ALTER TABLE public.georef_maps_id_seq OWNER TO postgres;

    --
    -- Name: jobs; Type: TABLE; Schema: public; Owner: postgres
    --

    CREATE TABLE public.jobs (
        id integer NOT NULL,
        processed boolean DEFAULT false,
        task character varying,
        submitted timestamp without time zone NOT NULL,
        user_id character varying NOT NULL,
        comment character varying DEFAULT ''::character varying,
        task_name character varying NOT NULL
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
        description character varying,
        measures character varying,
        scale character varying,
        type character varying,
        technic character varying,
        ppn character varying,
        permalink character varying,
        license character varying,
        owner character varying,
        link_jpg character varying,
        link_zoomify character varying,
        time_of_publication timestamp without time zone,
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
        enabled boolean,
        map_type character varying,
        default_srs integer DEFAULT 4326 NOT NULL,
        rel_path character varying,
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
        submitted timestamp without time zone NOT NULL,
        user_id character varying NOT NULL,
        params character varying NOT NULL,
        validation character varying NOT NULL,
        original_map_id integer NOT NULL,
        overwrites integer NOT NULL,
        comment character varying,
        clip public.geometry,
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
    -- Data for Name: georef_maps; Type: TABLE DATA; Schema: public; Owner: postgres
    --

    INSERT INTO public.georef_maps VALUES (10001556, 11823, './ae/df_dk_0010001_5154_1892.tif', '0103000020DA1000000100000005000000F5511DDDCE522D40DCBCA18B2E654940F5511DDDCE522D404288914939734940ABE732A2A5A82D404288914939734940ABE732A2A5A82D40DCBCA18B2E654940F5511DDDCE522D40DCBCA18B2E654940', '2018-02-23 11:17:53');
    INSERT INTO public.georef_maps VALUES (10007521, 12187, './gl/df_dk_0010002_0004.tif', '0103000020E6100000010000000500000093ABCA518F532C40FE437E269075494093ABCA518F532C40556764791FB449404FD056C065222E40556764791FB449404FD056C065222E40FE437E269075494093ABCA518F532C40FE437E2690754940', '2018-06-18 10:35:34');
    INSERT INTO public.georef_maps VALUES (10009405, 8968, './mb/df_dk_0002357.tif', '0103000020DA1000000100000005000000D62E7A622E442D40148B9185A57C4940D62E7A622E442D40510EE0D9D08749408CB0B0F91B8A2D40510EE0D9D08749408CB0B0F91B8A2D40148B9185A57C4940D62E7A622E442D40148B9185A57C4940', '2017-01-24 18:04:35');
    INSERT INTO public.georef_maps VALUES (10009482, 7912, './cm/dd_stad_0000007_0015.tif', '0103000020E61000000100000005000000BC2F01D4E1972B404E4D38AA09854940BC2F01D4E1972B407902EF51F0874940441503C628AA2B407902EF51F0874940441503C628AA2B404E4D38AA09854940BC2F01D4E1972B404E4D38AA09854940', '2016-06-29 14:51:34');
    INSERT INTO public.georef_maps VALUES (10001963, 12347, './mtb/df_dk_0010001_4948_1925.tif', '0103000020DA10000001000000050000002E3BE54D55552B40C52FB5D8FF7F49402E3BE54D55552B40B2A035E1CC8C49409D07E7BBAAAA2B40B2A035E1CC8C49409D07E7BBAAAA2B40C52FB5D8FF7F49402E3BE54D55552B40C52FB5D8FF7F4940', '2018-08-09 11:26:59');
    INSERT INTO public.georef_maps VALUES (10009466, 14624, './tkx/df_dk_0000006.tif', '0103000020DA10000001000000050000006C41A3FFDB542B4095FD1BFD6D8249406C41A3FFDB542B40F7D800E6868D4940A6AA316ABC9A2B40F7D800E6868D4940A6AA316ABC9A2B4095FD1BFD6D8249406C41A3FFDB542B4095FD1BFD6D824940', '2021-07-05 12:08:44');


    --
    -- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: postgres
    --


    --
    -- Data for Name: metadata; Type: TABLE DATA; Schema: public; Owner: postgres
    --

    INSERT INTO public.metadata VALUES (10001556, 'Äquidistantenkarte 107 : Section Zittau, 1892', 'Section Zittau', 'Topographische Karte (Äquidistantenkarte) Sachsen; 5154,1892', 'Section Zittau. - 1:25000. - Leipzig: Giesecke & Devrient, 1892. - 1 Kt.', '48 x 45 cm', '1:25000', 'Druckgraphik', 'Lithografie & Umdruck', 'ppn33592090X', 'http://digital.slub-dresden.de/id33592090X', '', 'Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dk/0010000/df_dk_0010001_5154_1892.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5154_1892/ImageProperties.xml', '1892-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010001_5154_1892.jpg', 'http://fotothek.slub-dresden.de/mids/df/dk/0010000/df_dk_0010001_5154_1892.jpg');
    INSERT INTO public.metadata VALUES (10007521, '6: Bischofswerda bis Görlitz, 1:120 000, 1846', 'Bischofswerda bis Görlitz', '', 'VI : Bautzen, Görlitz. - Bearb. u. lith. 1832 u. 1833. - [Ca. 1:120 000]. - Dresden : Williard , [1846]. - 1 Kt. : flächenkolor. , 52 x 45 cm. Kopftitel. - Verzeichnis der Höhenbestimmungen rechts u. Farberklärung links neben Kartenbild. - Mit je 2 Profilen über bzw. unter Kartenbild', NULL, '1:25000', 'Druckgrafik', '', 'ppn323661904', 'http://digital.slub-dresden.de/id323661904', 'CC-BY-SA', 'SLUB / Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dk/0010000/df_dk_0010002_0004.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010002_0004/ImageProperties.xml', '1846-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010002_0004.jpg', 'http://fotothek.slub-dresden.de/mids/df/dk/0010000/df_dk_0010002_0004.jpg');
    INSERT INTO public.metadata VALUES (10009405, '[Meilenblätter von Sachsen, Blatt 181 - 367] : Berliner Exemplar / [aufgenommen vom Sächs. Ing.-Korps 1780 - 1806 unter Ltg. von Friedrich Ludwig Aster]. - [1:12 000]. - 1 Kt. in 370 Teilen : mehrfarb. , je Bl. 57 x 57 cm Auch als Königsexemplar bezeichn. - Mit Höhenschraffen. - Nordwesten oben', 'Meilenblätter von Sachsen – Berliner Exemplar', '', 'Herrnhut, Obercunnersdorf, Strahwalde, Ruppersdorf, Oberoderwitz. Blatt 357 aus: Meilenblätter von Sachsen', '57 x 57 cm', '1:12000', 'Zeichenkunst
        ', '', '', 'http://www.deutschefotothek.de/list/freitext/df_dk_0002357', 'RV-FZ-PA', 'SLUB / Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dk/0002000/df_dk_0002357.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dk/0002000/df_dk_0002357/ImageProperties.xml', '1805-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dk/0002000/df_dk_0002357.jpg', 'http://fotothek.slub-dresden.de/mids/df/dk/0002000/df_dk_0002357.jpg');
    INSERT INTO public.metadata VALUES (10009482, 'Schadensplan der Stadt Dresden. Bearbeitet 1945/1946 vom Stadtbauamt Dresden. [Grundlagenkarte: Plan von Dresden. Blatt 1 [Altstadt, Neustadt], mit Legende zum Zerstörungsgrad (schwarz - total zerstört, blau - schwer beschädigt, grün - mittelschwer beschädigt, rot - leicht beschädigt)', 'Dresden [Altstadt, Neustadt]', '', 'Plan von Dresden. 1911/13/38/39/40. Blatt 1-12. 14-22, 24, 27, 29, 36, 39, 41-42. Bearb. Vom Vermessungsamt. 1:5000. 1.-9.,11., 13., 14. Aufl. Dresden 1911/13/38/39/40. 50 x 50 cm. Die Blätter 23, 25, 28 und 40 sind nur unter Schadensplan zu finden.', '50 x 50 cm', '1:5000', 'Druckgrafik
        ', '', 'ppn118692585', 'http://digital.slub-dresden.de/id118692585', 'RV-FZ-PA', 'Stadtarchiv Dresden', 'http://fotothek.slub-dresden.de/fotos/dd/stad/0000000/dd_stad_0000007_0015.jpg', 'http://fotothek.slub-dresden.de/zooms/dd/stad/0000000/dd_stad_0000007_0015/ImageProperties.xml', '1946-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/dd/stad/0000000/dd_stad_0000007_0015.jpg', 'http://fotothek.slub-dresden.de/mids/dd/stad/0000000/dd_stad_0000007_0015.jpg');
    INSERT INTO public.metadata VALUES (10001963, 'Meßtischblatt 66 : Dresden, 1925', 'Dresden', 'Topographische Karte (Meßtischblätter) Sachsen; 4948,1925', 'Dresden. - Umdr.-Ausg., aufgen. 1908/09, hrsg. 1910, Nachtr. 1925. - 1:25000. - Leipzig, 1925. - 1 Kt.', '48 x 45 cm', '1:25000', 'Druckgraphik', 'Lithografie & Umdruck', 'ppn335918751', 'http://digital.slub-dresden.de/id335918751', '', 'Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dk/0010000/df_dk_0010001_4948_1925.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_4948_1925/ImageProperties.xml', '1925-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010001_4948_1925.jpg', 'http://fotothek.slub-dresden.de/mids/df/dk/0010000/df_dk_0010001_4948_1925.jpg');
    INSERT INTO public.metadata VALUES (10007354, 'Section Dresden', 'Dresden', '', 'Section Dresden aus: Topographische Karte (Äquidistantenkarte) Sachsen', '46 x 44 cm', '1:25000', 'Druckgrafik', '', 'ppn11781931X', 'http://digital.slub-dresden.de/id11781931X', 'CC-BY-SA', 'SLUB / Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dk/0000000/df_dk_0000310.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dk/0000000/df_dk_0000310/ImageProperties.xml', '1887-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dk/0000000/df_dk_0000310.jpg', 'http://fotothek.slub-dresden.de/mids/df/dk/0000000/df_dk_0000310.jpg');
    INSERT INTO public.metadata VALUES (10009466, 'Sect. 09: Dresden', 'Dresden', '', 'Karte des Elbstromes innerhalb des Königreichs Sachsen : mit Angabe des durch das Hochwasser vom 31sten März 1845 erreichten Ueberschwemmungsgebietes , ... in 15 Sectionen und mit den von der Königlichen Wasserbau-Direction aufgenommenen Stromprofilen und Wassertiefen / bearb. von dem Königlich Sächsischen Finanzvermessungs-Bureau. [Lith. von W. Werner]. - 1:12 000 Dresden : Meinhold , 1850-1855. - 1 Kt. auf 15 Bl. : mehrfarb. , je Bl. 63 x 61 cm Nebensacht.: Karte des Elbstromes in Sachsen mit der Fluth 1845. - Lithogr. - Enth.: Sect. 1, Titelbl. mit Verbindungsnetz. Sect. 2/15, Kartenwerk. - Mit Höhenlage der Elb-Pegel und Brückenquerschnitten', '63 x 61 cm', '1:12000', 'Druckgrafik
        ', '', 'ppn118294873', 'http://digital.slub-dresden.de/id118294873', 'CC-BY-SA', 'SLUB / Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dk/0000000/df_dk_0000006.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dk/0000000/df_dk_0000006/ImageProperties.xml', '1855-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dk/0000000/df_dk_0000006.jpg', 'http://fotothek.slub-dresden.de/mids/df/dk/0000000/df_dk_0000006.jpg');
    INSERT INTO public.metadata VALUES (10010367, 'Plan von der Chur=Fürstl: Sæchs: Residenz Festung Alt und Neu Dresden, ...', 'Residenz Festung Alt und Neu Dresden', '', 'Sammlung von Festungsplänen. III. Grundrisse von denen Festungen in Teutschland nach seinen X. Hauptcreisen eingetheilet.', '62,4 x 72,5 cm', '1:0', 'Zeichenkunst
        ', '', '', 'http://www.deutschefotothek.de/list/freitext/df_dz_0000636', 'CC-BY-SA & PuD', 'SLUB / Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dz/0000000/df_dz_0000636.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dz/0000000/df_dz_0000636/ImageProperties.xml', '1732-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dz/0000000/df_dz_0000636.jpg', 'http://fotothek.slub-dresden.de/mids/df/dz/0000000/df_dz_0000636.jpg');
    INSERT INTO public.metadata VALUES (10003265, 'Meßtischblatt 2340 : Lissa, 1919', 'Lissa', 'Topographische Karte (Meßtischblätter); 4165,1919', 'Lissa. - Aufn. 1890, hrsg. 1891, Nachtr. 1919. - 1:25000. - [Berlin]: Reichsamt für Landesaufnahme, 1919. - 1 Kt.', '48 x 45 cm', '1:25000', 'Druckgraphik', 'Lithografie & Umdruck', 'ppn335948715', 'http://digital.slub-dresden.de/id335948715', '', 'Deutsche Fotothek', 'http://fotothek.slub-dresden.de/fotos/df/dk/0010000/df_dk_0010001_4165.jpg', 'http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_4165/ImageProperties.xml', '1919-01-01 00:00:00', 'http://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010001_4165.jpg', 'http://fotothek.slub-dresden.de/mids/df/dk/0010000/df_dk_0010001_4165.jpg');


    --
    -- Data for Name: original_maps; Type: TABLE DATA; Schema: public; Owner: postgres
    --

    INSERT INTO public.original_maps VALUES (10007521, 'df_dk_0010002_0004', true, 'GL', 4314, './gl/df_dk_0010002_0004.tif', NULL);
    INSERT INTO public.original_maps VALUES (10001963, 'df_dk_0010001_4948_1925', true, 'MTB', 4314, './mtb/df_dk_0010001_4948_1925.tif', NULL);
    INSERT INTO public.original_maps VALUES (10001556, 'df_dk_0010001_5154_1892', true, 'AE', 4314, './ae/df_dk_0010001_5154_1892.tif', NULL);
    INSERT INTO public.original_maps VALUES (10009482, 'dd_stad_0000007_0015', true, 'CM', 4326, './cm/dd_stad_0000007_0015.tif', NULL);
    INSERT INTO public.original_maps VALUES (10009405, 'df_dk_0002357', true, 'MB', 4314, './mb/df_dk_0002357.tif', NULL);
    INSERT INTO public.original_maps VALUES (10007354, 'df_dk_0000310', true, 'AE', 4314, './ae/df_dk_0000310.tif', NULL);
    INSERT INTO public.original_maps VALUES (10010367, 'df_dz_0000636', true, 'AK', 4326, './ak/df_dz_0000636.tif', NULL);
    INSERT INTO public.original_maps VALUES (10009466, 'df_dk_0000006', true, 'TKX', 4314, './tkx/df_dk_0000006.tif', NULL);
    INSERT INTO public.original_maps VALUES (10003265, 'df_dk_0010001_4165', true, 'MTB', 4314, './mtb/df_dk_0010001_4165.tif', NULL);


    --
    -- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
    --



    --
    -- Data for Name: transformations; Type: TABLE DATA; Schema: public; Owner: postgres
    --

    INSERT INTO public.transformations VALUES (6990, '2015-12-14 14:19:21', 'user_2', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "affine", "gcps": [{"source": [4215, 4225], "target": [13.738989332862, 51.054729594906]}, {"source": [5671, 7247], "target": [13.769041044263, 51.014073594726]}, {"source": [3483, 2432], "target": [13.72439149141, 51.078816150987]}, {"source": [5107, 3414], "target": [13.758749806377, 51.065411912287]}]}', 'valid', 10007354, 0, NULL, '0103000020DA1000000100000005000000AE75CA6802572B40043EE7F8CD8C49402B431531FEAD2B402DF870AEC18C49405A572F7C49AD2B40DAB54686B17F4940B17BE3CE42562B4080545C77C07F4940AE75CA6802572B40043EE7F8CD8C4940');
    INSERT INTO public.transformations VALUES (11229, '2017-11-06 17:21:13', 'user_1', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "tps", "gcps": [{"source": [5494, 7092], "target": [13.767304118408, 51.012843412447]}, {"source": [3352, 2256], "target": [13.722658749289, 51.077577984836]}, {"source": [4972, 3252], "target": [13.757012482328, 51.064175771823]}, {"source": [1025, 7440], "target": [13.672689198149, 51.008941746734]}, {"source": [1563, 7069], "target": [13.683868645314, 51.014058399564]}, {"source": [882, 7905], "target": [13.669964073795, 51.002798317601]}, {"source": [8436, 8198], "target": [13.82927656037, 50.999132125548]}, {"source": [7885, 1003], "target": [13.818547724251, 51.093779502957]}, {"source": [1008, 783], "target": [13.673268555236, 51.097370834337]}, {"source": [1002, 1801], "target": [13.672195671639, 51.083960875476]}, {"source": [8525, 1986], "target": [13.832103608615, 51.080884122992]}, {"source": [8506, 5277], "target": [13.831553755796, 51.037584021843]}, {"source": [8605, 5935], "target": [13.833922146362, 51.028460298251]}, {"source": [8114, 7743], "target": [13.822753428045, 51.004857469626]}, {"source": [4075, 7787], "target": [13.737405537232, 51.003919047747]}, {"source": [2233, 4813], "target": [13.698610066033, 51.043532282194]}, {"source": [1016, 3003], "target": [13.672544358823, 51.067806484896]}, {"source": [1035, 4119], "target": [13.672694562537, 51.052897515435]}, {"source": [3667, 1062], "target": [13.728881476927, 51.09354029558]}, {"source": [2937, 6211], "target": [13.713335393531, 51.024772515593]}, {"source": [8699, 1191], "target": [13.835724590775, 51.091266078903]}, {"source": [6273, 4221], "target": [13.784489034226, 51.05138005126]}, {"source": [4831, 5502], "target": [13.753461240368, 51.034370935322]}, {"source": [6442, 1969], "target": [13.787868617562, 51.081015554728]}, {"source": [4067, 4057], "target": [13.737347423812, 51.05350954619]}, {"source": [4258, 4176], "target": [13.741622418056, 51.051954165358]}, {"source": [3895, 4096], "target": [13.733771592269, 51.052994463798]}, {"source": [3975, 4002], "target": [13.735480606338, 51.054224413733]}, {"source": [4470, 3356], "target": [13.746182620307, 51.062869390761]}, {"source": [4804, 2258], "target": [13.753534108291, 51.077354705538]}, {"source": [5722, 799], "target": [13.772601932178, 51.096509244434]}, {"source": [4931, 2833], "target": [13.756143897663, 51.069755726474]}, {"source": [3158, 3611], "target": [13.718196451446, 51.059494535251]}, {"source": [3102, 3892], "target": [13.716972693746, 51.055786883555]}, {"source": [3031, 3521], "target": [13.715525641983, 51.060737377168]}, {"source": [3599, 4417], "target": [13.72745230783, 51.048755564945]}, {"source": [4150, 4921], "target": [13.739173561225, 51.042136778876]}, {"source": [5262, 5250], "target": [13.762846737991, 51.037854721518]}, {"source": [8382, 3419], "target": [13.829073607703, 51.062097342622]}, {"source": [6953, 4224], "target": [13.799080699573, 51.051411245061]}, {"source": [6607, 4203], "target": [13.79171647126, 51.051590392602]}, {"source": [8163, 7133], "target": [13.823752105018, 51.01283835281]}, {"source": [6993, 7156], "target": [13.799076675932, 51.012401287807]}, {"source": [1266, 4948], "target": [13.677367865821, 51.042033062983]}, {"source": [2420, 1308], "target": [13.702612370143, 51.090240961253]}, {"source": [844, 8302], "target": [13.669288605342, 50.997569855841]}, {"source": [8735, 8315], "target": [13.835564553519, 50.997658478761]}, {"source": [8703, 682], "target": [13.835751861225, 51.097937640504]}, {"source": [3642, 5133], "target": [13.728389516418, 51.039270171623]}, {"source": [4146, 4423], "target": [13.739192783614, 51.048731115119]}, {"source": [4322, 5546], "target": [13.742641657482, 51.033805038916]}, {"source": [6499, 7165], "target": [13.788948654692, 51.012165034738]}, {"source": [4008, 6274], "target": [13.73602330641, 51.024144923212]}, {"source": [3999, 6345], "target": [13.735759444507, 51.023062431283]}, {"source": [5197, 4176], "target": [13.761586099754, 51.051898524751]}, {"source": [6902, 3262], "target": [13.797688633094, 51.064075479497]}, {"source": [6984, 3298], "target": [13.799472302089, 51.063679353189]}, {"source": [6742, 3211], "target": [13.794237077018, 51.064814625268]}, {"source": [5301, 8294], "target": [13.763510584395, 50.997609525169]}, {"source": [6562, 8301], "target": [13.790476619979, 50.997631469889]}, {"source": [3443, 8295], "target": [13.723898827811, 50.997597708777]}, {"source": [2269, 8298], "target": [13.699051737349, 50.997582516268]}, {"source": [838, 6355], "target": [13.669213950416, 51.02340428467]}, {"source": [841, 7046], "target": [13.669246136924, 51.014333455228]}, {"source": [831, 5101], "target": [13.669020384441, 51.040023627129]}, {"source": [813, 671], "target": [13.668661415359, 51.098827839083]}, {"source": [818, 1594], "target": [13.66874277548, 51.08667350595]}, {"source": [820, 2570], "target": [13.668827712318, 51.073110452909]}, {"source": [3993, 671], "target": [13.736055492918, 51.098485910531]}, {"source": [7228, 677], "target": [13.804670870086, 51.098106922727]}, {"source": [8709, 3405], "target": [13.835690170417, 51.062174042304]}, {"source": [8715, 5446], "target": [13.835639655372, 51.035425123095]}, {"source": [8718, 6072], "target": [13.835623562118, 51.026997705065]}, {"source": [8728, 7420], "target": [13.835596293102, 51.009354374664]}]}', 'valid', 10007354, 11226, NULL, '0103000020E610000001000000050000008D51FC335A562B40E8A72172A68C49406A65FE6DE8AB2B40158DCC5B898C49400431FCA3D0AB2B40F61A18FFB27F4940CEB1FD59AC562B402A4EE92CB07F49408D51FC335A562B40E8A72172A68C4940');
    INSERT INTO public.transformations VALUES (8616, '2016-12-09 11:33:35', 'user_1', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "tps", "gcps": [{"source": [5684, 5464], "target": [13.734548985958, 51.052199489057]}, {"source": [5303, 5159], "target": [13.732971847057, 51.053811343032]}, {"source": [6674, 6055], "target": [13.739202618599, 51.048746290875]}, {"source": [7181, 4942], "target": [13.744371235371, 51.052051114741]}, {"source": [6406, 5215], "target": [13.739446699619, 51.052094952657]}, {"source": [5417, 3363], "target": [13.737410902977, 51.059772691986]}, {"source": [4887, 6725], "target": [13.727463930845, 51.048747977069]}, {"source": [8637, 4836], "target": [13.752852380276, 51.050445944031]}, {"source": [4368, 5579], "target": [13.726759850979, 51.053548324666]}, {"source": [6660, 5411], "target": [13.740439116955, 51.051086670104]}, {"source": [3562, 4690], "target": [13.724217116833, 51.05792165391]}, {"source": [2110, 4552], "target": [13.716446757317, 51.060433518255]}]}', 'invalid', 10010367, 0, NULL, '0103000020E6100000010000000500000031C4FF4F9D6F2B403E9AA8AD8A89494082BDFF5355682B405F190DFD508649408343005497802B40B8F26AA5DD84494050BAFF0F01882B408D6C02E31488494031C4FF4F9D6F2B403E9AA8AD8A894940');
    INSERT INTO public.transformations VALUES (14624, '2021-07-05 12:08:44', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [5549, 5002], "target": [13.740504826908, 51.049994444427]}, {"source": [7801, 4766], "target": [13.764599582931, 51.0390818907]}, {"source": [3508, 5076], "target": [13.719875986978, 51.060668337298]}, {"source": [523, 6779], "target": [13.676179225986, 51.066202092908]}, {"source": [1090, 2738], "target": [13.716912734929, 51.088199257554]}, {"source": [3838, 2775], "target": [13.743201705342, 51.072997727073]}, {"source": [4814, 3198], "target": [13.748968677725, 51.065113243408]}, {"source": [7891, 5262], "target": [13.760964516572, 51.035448473379]}, {"source": [4408, 5925], "target": [13.721273240668, 51.050372478208]}, {"source": [5592, 5254], "target": [13.738640347955, 51.048173140486]}, {"source": [6793, 994], "target": [13.787341121151, 51.068176154053]}, {"source": [6783, 4942], "target": [13.753139661684, 51.043626029468]}, {"source": [1888, 3509], "target": [13.717945194694, 51.0789982614]}, {"source": [1854, 6761], "target": [13.689412241719, 51.058696130125]}, {"source": [5101, 4606], "target": [13.739678768356, 51.054921811545]}, {"source": [5666, 2452], "target": [13.763692502646, 51.065317431612]}, {"source": [4592, 4050], "target": [13.739421023678, 51.06111736439]}, {"source": [5454, 4576], "target": [13.74335063344, 51.053191889555]}, {"source": [5319, 4674], "target": [13.741178733743, 51.053326893317]}, {"source": [5128, 4873], "target": [13.737508026718, 51.05311054341]}, {"source": [5036, 4913], "target": [13.73627594047, 51.053432427674]}, {"source": [4816, 4844], "target": [13.734704999704, 51.055047648919]}, {"source": [4897, 5558], "target": [13.729191385059, 51.04998618123]}, {"source": [6101, 5575], "target": [13.740902947934, 51.04337125108]}, {"source": [5916, 5941], "target": [13.735784933245, 51.042036905382]}, {"source": [1557, 5119], "target": [13.700516440786, 51.070648928631]}, {"source": [1241, 4778], "target": [13.700657865132, 51.074420657627]}, {"source": [1401, 4922], "target": [13.700842452039, 51.072660683052]}, {"source": [1083, 4796], "target": [13.699018822197, 51.075207239842]}, {"source": [1318, 4505], "target": [13.703719661758, 51.075724043896]}, {"source": [936, 3268], "target": [13.710827147145, 51.085592308973]}, {"source": [409, 2962], "target": [13.708159700918, 51.090468878656]}, {"source": [412, 3273], "target": [13.705731875615, 51.088678942737]}, {"source": [414, 3441], "target": [13.704194923497, 51.087544260428]}]}', 'missing', 10009466, 7926, NULL, '0103000020DA10000001000000090000002D8F4DE41D752B40093400E6868D4940FF73937675602B40F40F5BE8B58949406C41A3FFDB542B40396E89409B874940321AA1725F7A2B4082A21CFD6D824940743C7E61CD952B4049AB606771874940A9D2DAE124992B404F098CDD0C884940472ED17B50992B40CD944DEE14884940D8F22F6ABC9A2B40AF244F53588849402D8F4DE41D752B40093400E6868D4940');
    INSERT INTO public.transformations VALUES (8617, '2016-12-09 11:57:19', 'user_1', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "tps", "gcps": [{"source": [5684, 5464], "target": [13.734548985958, 51.052199489057]}, {"source": [5303, 5159], "target": [13.732971847057, 51.053811343032]}, {"source": [6674, 6055], "target": [13.739202618599, 51.048746290875]}, {"source": [7181, 4942], "target": [13.744371235371, 51.052051114741]}, {"source": [6406, 5215], "target": [13.739446699619, 51.052094952657]}, {"source": [5417, 3363], "target": [13.737410902977, 51.059772691986]}, {"source": [4887, 6725], "target": [13.727463930845, 51.048747977069]}, {"source": [8637, 4836], "target": [13.752852380276, 51.050445944031]}, {"source": [4368, 5579], "target": [13.726759850979, 51.053548324666]}, {"source": [6660, 5411], "target": [13.740439116955, 51.051086670104]}, {"source": [3562, 4690], "target": [13.724217116833, 51.05792165391]}, {"source": [2110, 4552], "target": [13.716446757317, 51.060433518255]}, {"source": [4278, 8050], "target": [13.721344470978, 51.045151184076]}, {"source": [6045, 8046], "target": [13.731558322906, 51.042702574497]}, {"source": [9468, 1186], "target": [13.765246868134, 51.062638451947]}, {"source": [7232, 820], "target": [13.753021359444, 51.066656960047]}, {"source": [5849, 839], "target": [13.745119571686, 51.068457084591]}, {"source": [4837, 858], "target": [13.739165067673, 51.069862751143]}]}', 'valid', 10010367, 8616, NULL, '0103000020E6100000010000000700000027580030AE6F2B40FDEE77129389494029C5FF3F846B2B40DFE95A2BBD874940192D00C043682B408A66ABF456864940F0C1FF1FAD802B40E83861C0DE844940FF1B005426882B4062F9203828884940760700E89A7F2B40C20E00F1A388494027580030AE6F2B40FDEE771293894940');
    INSERT INTO public.transformations VALUES (11820, '2018-02-22 19:21:33', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [6700, 998], "target": [14.809598143882, 50.897193142054]}, {"source": [6656, 944], "target": [14.808447340273, 50.898010360894]}, {"source": [6687, 1160], "target": [14.809553413595, 50.894672082697]}, {"source": [6969, 3160], "target": [14.816612770199, 50.86360605225]}, {"source": [1907, 1301], "target": [14.690521820736, 50.89186048425]}, {"source": [4180, 4396], "target": [14.747856878332, 50.843955583957]}, {"source": [5070, 5489], "target": [14.7697720894, 50.82712525216]}, {"source": [6933, 7171], "target": [14.816342009147, 50.801483296267]}, {"source": [3325, 7152], "target": [14.727274236933, 50.80102696424]}, {"source": [1509, 6622], "target": [14.681454721869, 50.808715848793]}, {"source": [2416, 3598], "target": [14.703546133685, 50.856059149161]}, {"source": [7395, 946], "target": [14.826504194817, 50.89826554693]}, {"source": [946, 6862], "target": [14.6663422656, 50.805188343225]}, {"source": [771, 7207], "target": [14.661734802203, 50.799776766279]}, {"source": [7465, 7231], "target": [14.829386735822, 50.800594679559]}, {"source": [788, 781], "target": [14.663646847302, 50.899831455195]}, {"source": [7486, 818], "target": [14.82913212475, 50.900185562006]}, {"source": [7484, 939], "target": [14.829138207254, 50.898323451967]}, {"source": [7483, 1160], "target": [14.829145690246, 50.894908649985]}, {"source": [7478, 2392], "target": [14.829196333407, 50.874764135456]}, {"source": [7471, 3849], "target": [14.829253980594, 50.852910619034]}, {"source": [7465, 6803], "target": [14.829363595071, 50.807345464462]}, {"source": [7464, 5611], "target": [14.829323127724, 50.825911025074]}, {"source": [7072, 816], "target": [14.818461583571, 50.900162260357]}, {"source": [6816, 815], "target": [14.812297815235, 50.900151363045]}, {"source": [6421, 813], "target": [14.802223055401, 50.900129108943]}, {"source": [6618, 814], "target": [14.807439743386, 50.900140444579]}, {"source": [6095, 811], "target": [14.793961369783, 50.900113592786]}, {"source": [5696, 809], "target": [14.783920386271, 50.90009006901]}, {"source": [4628, 802], "target": [14.757753787373, 50.900032967922]}, {"source": [4315, 798], "target": [14.750505881466, 50.900016166096]}, {"source": [4392, 801], "target": [14.752365901331, 50.900022903533]}, {"source": [2144, 787], "target": [14.696740416279, 50.899902829452]}, {"source": [2730, 789], "target": [14.711380114007, 50.899935585853]}, {"source": [1454, 894], "target": [14.678838243649, 50.898270459211]}, {"source": [2110, 787], "target": [14.695619332092, 50.899901155554]}, {"source": [1729, 786], "target": [14.685688822736, 50.899880166419]}, {"source": [788, 1240], "target": [14.663512311177, 50.892726857808]}, {"source": [788, 910], "target": [14.663606155606, 50.897668381631]}, {"source": [786, 2712], "target": [14.663059848302, 50.869356443969]}, {"source": [782, 3878], "target": [14.662716362387, 50.851226911849]}, {"source": [776, 4935], "target": [14.662403925839, 50.835015827591]}, {"source": [775, 6249], "target": [14.662018099098, 50.814587800198]}, {"source": [1129, 7208], "target": [14.671402657728, 50.799822389981]}, {"source": [2847, 7216], "target": [14.714946176897, 50.800035323499]}, {"source": [5029, 7222], "target": [14.769027446006, 50.800301491259]}, {"source": [6878, 7228], "target": [14.814811179832, 50.800522858337]}, {"source": [2344, 5329], "target": [14.702654428009, 50.828966503343]}, {"source": [3227, 5703], "target": [14.724240371031, 50.8232759546]}, {"source": [3401, 5702], "target": [14.728240876935, 50.823645317217]}, {"source": [3564, 6419], "target": [14.73272572274, 50.812001814472]}, {"source": [5055, 6582], "target": [14.769530818319, 50.809901029415]}, {"source": [5040, 6641], "target": [14.769256301389, 50.808950067451]}, {"source": [6587, 5689], "target": [14.807585453948, 50.824413388403]}, {"source": [5454, 6101], "target": [14.779585656235, 50.817950251382]}, {"source": [4307, 6647], "target": [14.751634274369, 50.808613015651]}, {"source": [5574, 7223], "target": [14.78229608579, 50.800354684715]}]}', 'valid', 10001556, 0, NULL, '0103000020DA100000010000000B0000002545398FC9532D403562E4B02D734940B07C28DDCE522D40F8ADC7155F664940AAEA8D2D97872D400DD3D4796F6649405246679732882D409FD873EB6F664940B4FD42C742882D40782CA58B2E654940EF2FA5679F902D401D0D4434316549407E12F8F388902D4050E5272272664940D03943A2A5A82D40E71DEFE2796649409962251E84A82D40E4C0944939734940D00622C483A82D40E4C09449397349402545398FC9532D403562E4B02D734940');
    INSERT INTO public.transformations VALUES (11823, '2018-02-23 11:17:53', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]}, {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}, {"source": [6969, 3160], "target": [14.816612768409, 50.863606051111]}, {"source": [1907, 1301], "target": [14.690521818997, 50.891860483128]}, {"source": [4180, 4396], "target": [14.747856876595, 50.843955582846]}, {"source": [5070, 5489], "target": [14.769772087663, 50.827125251053]}, {"source": [6933, 7171], "target": [14.816342007402, 50.801483295161]}, {"source": [3325, 7152], "target": [14.727274235239, 50.801026963158]}, {"source": [1509, 6622], "target": [14.681454720195, 50.808715847718]}, {"source": [2416, 3598], "target": [14.703546131965, 50.856059148055]}, {"source": [7395, 946], "target": [14.826504192996, 50.898265545769]}, {"source": [946, 6862], "target": [14.666342263936, 50.805188342156]}, {"source": [771, 7207], "target": [14.661734800546, 50.799776765214]}, {"source": [7465, 7231], "target": [14.82938673407, 50.80059467845]}, {"source": [788, 781], "target": [14.663646845572, 50.899831454076]}, {"source": [7486, 818], "target": [14.829132122927, 50.900185560843]}, {"source": [7484, 939], "target": [14.829138205432, 50.898323450806]}, {"source": [7483, 1160], "target": [14.829145688426, 50.894908648825]}, {"source": [7478, 2392], "target": [14.829196331602, 50.874764134307]}, {"source": [7471, 3849], "target": [14.829253978805, 50.852910617897]}, {"source": [7465, 6803], "target": [14.829363593315, 50.80734546335]}, {"source": [7464, 5611], "target": [14.829323125954, 50.825911023952]}, {"source": [7072, 816], "target": [14.818461581754, 50.900162259197]}, {"source": [6816, 815], "target": [14.812297813421, 50.900151361887]}, {"source": [6421, 813], "target": [14.802223053593, 50.900129107788]}, {"source": [6618, 814], "target": [14.807439741575, 50.900140443422]}, {"source": [6095, 811], "target": [14.79396136798, 50.900113591633]}, {"source": [5696, 809], "target": [14.783920384473, 50.900090067859]}, {"source": [4628, 802], "target": [14.75775378559, 50.900032966778]}, {"source": [4315, 798], "target": [14.750505879687, 50.900016164954]}, {"source": [4392, 801], "target": [14.752365899551, 50.900022902391]}, {"source": [2144, 787], "target": [14.696740414531, 50.899902828324]}, {"source": [2730, 789], "target": [14.711380112251, 50.899935584721]}, {"source": [1454, 894], "target": [14.678838241912, 50.898270458088]}, {"source": [2110, 787], "target": [14.695619330344, 50.899901154426]}, {"source": [1729, 786], "target": [14.685688820994, 50.899880165294]}, {"source": [788, 1240], "target": [14.663512309453, 50.892726856692]}, {"source": [788, 910], "target": [14.663606153878, 50.897668380513]}, {"source": [786, 2712], "target": [14.663059846595, 50.869356442866]}, {"source": [782, 3878], "target": [14.662716360693, 50.851226910756]}, {"source": [776, 4935], "target": [14.662403924156, 50.835015826507]}, {"source": [775, 6249], "target": [14.66201809743, 50.814587799125]}, {"source": [1129, 7208], "target": [14.671402656065, 50.799822388914]}, {"source": [2847, 7216], "target": [14.71494617521, 50.80003532242]}, {"source": [5029, 7222], "target": [14.769027444289, 50.800301490166]}, {"source": [6878, 7228], "target": [14.814811178089, 50.800522857232]}, {"source": [2344, 5329], "target": [14.702654426308, 50.828966502252]}, {"source": [3227, 5703], "target": [14.724240369322, 50.823275953506]}, {"source": [3401, 5702], "target": [14.728240875224, 50.823645316122]}, {"source": [3564, 6419], "target": [14.732725721035, 50.812001813382]}, {"source": [5055, 6582], "target": [14.769530816595, 50.809901028317]}, {"source": [5040, 6641], "target": [14.769256299665, 50.808950066353]}, {"source": [6587, 5689], "target": [14.807585452192, 50.824413387287]}, {"source": [5454, 6101], "target": [14.779585654499, 50.817950250277]}, {"source": [4307, 6647], "target": [14.751634272656, 50.808613014558]}, {"source": [5574, 7223], "target": [14.782296084065, 50.800354683619]}, {"source": [1354, 784], "target": [14.67634612815, 50.899859802211]}, {"source": [2389, 787], "target": [14.701935480532, 50.899914589163]}, {"source": [3824, 1662], "target": [14.738689286797, 50.886536375438]}, {"source": [3224, 1988], "target": [14.724086779327, 50.881400957462]}, {"source": [5561, 1866], "target": [14.781628702951, 50.883739028779]}, {"source": [4983, 2643], "target": [14.767642016105, 50.871542857]}, {"source": [4726, 2993], "target": [14.761426208635, 50.866146613586]}, {"source": [1752, 2466], "target": [14.686777727172, 50.873739758153]}, {"source": [2120, 3274], "target": [14.695887327077, 50.860745617059]}, {"source": [6153, 3355], "target": [14.796487598134, 50.860512023302]}, {"source": [2581, 6592], "target": [14.708445231744, 50.809621467831]}, {"source": [3009, 3992], "target": [14.718511063861, 50.849750438399]}, {"source": [7188, 7229], "target": [14.822605684397, 50.800558336973]}, {"source": [4111, 3785], "target": [14.745949775376, 50.85370368877]}, {"source": [4006, 3615], "target": [14.743331660827, 50.856337080476]}, {"source": [3893, 3472], "target": [14.740705479905, 50.858508042521]}, {"source": [3737, 4589], "target": [14.737042129051, 50.840928706352]}, {"source": [5695, 4687], "target": [14.785700030341, 50.840037938729]}, {"source": [3367, 793], "target": [14.727518573288, 50.899969586806]}, {"source": [789, 1410], "target": [14.663452240739, 50.889766853181]}, {"source": [783, 3619], "target": [14.662793178389, 50.855212017021]}, {"source": [6387, 7226], "target": [14.802360083153, 50.800460327448]}, {"source": [7467, 4470], "target": [14.829268312941, 50.843462199227]}]}', 'valid', 10001556, 11820, NULL, '0103000020DA100000010000000B000000CEAA2A8FC9532D407A05E2B02D73494059E219DDCE522D403D51C5155F66494053507F2D97872D405176D2796F664940FCAB589732882D40E47B71EB6F6649405D6334C742882D40BDCFA28B2E654940989596679F902D4061B04134316549402778E9F388902D40948825227266494092C333A2A5A82D402BC1ECE2796649405BEC151E84A82D402F2D924939734940929012C483A82D402F2D924939734940CEAA2A8FC9532D407A05E2B02D734940');
    INSERT INTO public.transformations VALUES (7758, '2016-05-09 10:52:18', 'user_2', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "affine", "gcps": [{"source": [3195, 3986], "target": [14.42561262705, 51.183689473957]}, {"source": [5223, 5048], "target": [14.668943094563, 51.101568233786]}, {"source": [7907, 4149], "target": [14.994077170632, 51.159581323447]}, {"source": [1665, 1321], "target": [14.246610357359, 51.387001187134]}]}', 'valid', 10007521, 0, NULL, '0103000020DA10000001000000050000007CCD7C947B592C408E8B5C0B49B449401F6C257B1A222E4077F0B5DE8DB14940FE317CA688192E40D0AAB0C878754940560691E929512C4059B13EB5287849407CCD7C947B592C408E8B5C0B49B44940');
    INSERT INTO public.transformations VALUES (18, '2021-10-04 17:27:12.554384', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]}, {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}, {"source": [6969, 3160], "target": [14.816612768409, 50.863606051111]}, {"source": [1907, 1301], "target": [14.690521818997, 50.891860483128]}, {"source": [4180, 4396], "target": [14.747856876595, 50.843955582846]}, {"source": [5070, 5489], "target": [14.769772087663, 50.827125251053]}, {"source": [6933, 7171], "target": [14.816342007402, 50.801483295161]}, {"source": [3325, 7152], "target": [14.727274235239, 50.801026963158]}, {"source": [1509, 6622], "target": [14.681454720195, 50.808715847718]}]}', 'missing', 10001556, 11823, NULL, '0103000020DA100000010000000B000000CEAA2A8FC9532D4080CEE1B02D734940F5511DDDCE522D4049E3C4155F664940D69B832D97872D403289D3796F6649402EF4569732882D40F00D71EB6F6649402B1B36C742882D40DCBCA18B2E6549407F7197679F902D40551E423431654940F52FEBF388902D40B475242272664940ABE732A2A5A82D404BAEEBE2796649401080181E84A82D404288914939734940ABB411C483A82D404288914939734940CEAA2A8FC9532D4080CEE1B02D734940');
    INSERT INTO public.transformations VALUES (12180, '2018-06-13 15:01:14', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [3195, 3986], "target": [14.425612623442, 51.183689471521]}, {"source": [5223, 5048], "target": [14.668943090803, 51.101568231318]}, {"source": [7907, 4149], "target": [14.994077166404, 51.159581320741]}, {"source": [1665, 1321], "target": [14.246610353649, 51.387001184551]}, {"source": [1066, 1047], "target": [14.175884499064, 51.408678698035]}, {"source": [1033, 7382], "target": [14.164487568014, 50.926844974102]}, {"source": [7424, 6055], "target": [14.932199803967, 51.019574181517]}, {"source": [6566, 5685], "target": [14.828911953001, 51.048388028077]}, {"source": [7915, 6568], "target": [14.990833025557, 50.979407052335]}, {"source": [7654, 1847], "target": [14.971861873241, 51.336974669044]}, {"source": [6447, 2387], "target": [14.825617155189, 51.295987201865]}, {"source": [6097, 1061], "target": [14.788533193496, 51.399713860947]}, {"source": [2842, 7384], "target": [14.379821581008, 50.925120001999]}, {"source": [2017, 6717], "target": [14.280181521541, 50.976381244353]}, {"source": [3481, 6313], "target": [14.452862997387, 51.006070886406]}, {"source": [4564, 7390], "target": [14.584001495473, 50.923495622454]}, {"source": [5862, 7393], "target": [14.744912569212, 50.922164594838]}, {"source": [5869, 6127], "target": [14.745651428538, 51.0169882168]}, {"source": [8447, 2960], "target": [15.063407020674, 51.251012182362]}, {"source": [8432, 5159], "target": [15.056776081041, 51.082331653744]}, {"source": [8428, 5994], "target": [15.054328030997, 51.020028166673]}]}', 'valid', 10007521, 12140, NULL, '0103000020DA100000010000000500000000E15D947B592C4031F6560B49B44940F6E4B5A064232E4068852294B0B24940819A97D0CF192E408B2D3974B775494066A129347A542C40F8DB7031A576494000E15D947B592C4031F6560B49B44940');
    INSERT INTO public.transformations VALUES (12187, '2018-06-18 10:35:34', 'user_1', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "tps", "gcps": [{"source": [3195, 3986], "target": [14.423772091223, 51.182450164502]}, {"source": [5223, 5048], "target": [14.667069906319, 51.100342060004]}, {"source": [7907, 4149], "target": [14.992153638221, 51.158353878838]}, {"source": [1665, 1321], "target": [14.244788283506, 51.385736107192]}, {"source": [1066, 1047], "target": [14.174072089556, 51.407410074107]}, {"source": [1033, 7382], "target": [14.16269562121, 50.925630625192]}, {"source": [7424, 6055], "target": [14.93029117575, 51.018361521668]}, {"source": [6566, 5685], "target": [14.827017348711, 51.047170436648]}, {"source": [7915, 6568], "target": [14.988917426925, 50.978199883212]}, {"source": [7654, 1847], "target": [14.969934221571, 51.335726845121]}, {"source": [6447, 2387], "target": [14.823712866835, 51.294741612028]}, {"source": [6097, 1061], "target": [14.786630105084, 51.398455958985]}, {"source": [2842, 7384], "target": [14.377998005447, 50.923909181003]}, {"source": [2017, 6717], "target": [14.278370618292, 50.975163083527]}, {"source": [3481, 6313], "target": [14.451025486398, 51.004852068203]}, {"source": [4564, 7390], "target": [14.582147954979, 50.922288199165]}, {"source": [5862, 7393], "target": [14.743035433885, 50.920959891845]}, {"source": [5869, 6127], "target": [14.743770359086, 51.015772824239]}, {"source": [8447, 2960], "target": [15.061469434251, 51.249775568628]}, {"source": [8432, 5159], "target": [15.054846524671, 51.081113959285]}, {"source": [8428, 5994], "target": [15.05240142141, 51.018817459452]}, {"source": [1166, 4703], "target": [14.179809093475, 51.127778830973]}, {"source": [5120, 3759], "target": [14.658204675507, 51.197063252325]}]}', 'valid', 10007521, 12185, NULL, '0103000020E610000001000000050000005A08D20B8E582C403C4365791FB4494036AC57C065222E401524398687B2494022ACB9E8D3182E40F77A7E269075494016F7CE518F532C402ECFBD667D7649405A08D20B8E582C403C4365791FB44940');
    INSERT INTO public.transformations VALUES (12140, '2018-06-06 09:52:56', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [3195, 3986], "target": [14.425612625246, 51.183689472739]}, {"source": [5223, 5048], "target": [14.668943092683, 51.101568232552]}, {"source": [7907, 4149], "target": [14.994077168518, 51.159581322094]}, {"source": [1665, 1321], "target": [14.246610355504, 51.387001185843]}, {"source": [1066, 1047], "target": [14.175884500897, 51.408678699321]}, {"source": [1033, 7382], "target": [14.164487569496, 50.926844975109]}, {"source": [7424, 6055], "target": [14.932199805938, 51.019574182773]}, {"source": [6566, 5685], "target": [14.828911954933, 51.048388029322]}, {"source": [7915, 6568], "target": [14.990833027533, 50.979407053584]}, {"source": [7654, 1847], "target": [14.971861875478, 51.336974670496]}, {"source": [6447, 2387], "target": [14.825617157306, 51.295987203253]}, {"source": [6097, 1061], "target": [14.788533195671, 51.399713862388]}, {"source": [2842, 7384], "target": [14.379821582601, 50.92512000306]}]}', 'valid', 10007521, 7758, NULL, '0103000020DA10000001000000050000003E576D947B592C40E0C0590B49B449406AED5607E2232E4075E9D57BA7B249408DC8A8D0CF192E4040C13B74B7754940EF8336347A542C40BA017331A57649403E576D947B592C40E0C0590B49B44940');
    INSERT INTO public.transformations VALUES (12185, '2018-06-15 17:29:14', 'user_1', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "tps", "gcps": [{"source": [3195, 3986], "target": [14.423772091223, 51.182450164502]}, {"source": [5223, 5048], "target": [14.667069906319, 51.100342060004]}, {"source": [7907, 4149], "target": [14.992153638221, 51.158353878838]}, {"source": [1665, 1321], "target": [14.244788283506, 51.385736107192]}, {"source": [1066, 1047], "target": [14.174072089556, 51.407410074107]}, {"source": [1033, 7382], "target": [14.16269562121, 50.925630625192]}, {"source": [7424, 6055], "target": [14.93029117575, 51.018361521668]}, {"source": [6566, 5685], "target": [14.827017348711, 51.047170436648]}, {"source": [7915, 6568], "target": [14.988917426925, 50.978199883212]}, {"source": [7654, 1847], "target": [14.969934221571, 51.335726845121]}, {"source": [6447, 2387], "target": [14.823712866835, 51.294741612028]}, {"source": [6097, 1061], "target": [14.786630105084, 51.398455958985]}, {"source": [2842, 7384], "target": [14.377998005447, 50.923909181003]}, {"source": [2017, 6717], "target": [14.278370618292, 50.975163083527]}, {"source": [3481, 6313], "target": [14.451025486398, 51.004852068203]}, {"source": [4564, 7390], "target": [14.582147954979, 50.922288199165]}, {"source": [5862, 7393], "target": [14.743035433885, 50.920959891845]}, {"source": [5869, 6127], "target": [14.743770359086, 51.015772824239]}, {"source": [8447, 2960], "target": [15.061469434251, 51.249775568628]}, {"source": [8432, 5159], "target": [15.054846524671, 51.081113959285]}, {"source": [8428, 5994], "target": [15.05240142141, 51.018817459452]}, {"source": [1166, 4703], "target": [14.179809093475, 51.127778830973]}]}', 'valid', 10007521, 12180, NULL, '0103000020E610000001000000050000005A08D20B8E582C403C4365791FB4494036AC57C065222E401524398687B2494022ACB9E8D3182E40F77A7E269075494016F7CE518F532C402ECFBD667D7649405A08D20B8E582C403C4365791FB44940');
    INSERT INTO public.transformations VALUES (33, '2021-11-22 15:56:02.77124', 'test', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "affine", "gcps": [{"source": [3038, 3551], "target": [13.808341920376002, 51.053044201955004]}, {"source": [4998, 3553], "target": [13.817241489886998, 51.053121759652015]}, {"source": [4565, 3052], "target": [13.815058171749, 51.05438964098204]}, {"source": [4810, 2511], "target": [13.816431462765, 51.05612954927801]}, {"source": [766, 5503], "target": [13.798061013222, 51.047474882557]}, {"source": [4975, 8190], "target": [13.817291110754002, 51.039806066528996]}, {"source": [2962, 8280], "target": [13.808073699474, 51.039466231454014]}, {"source": [2468, 8281], "target": [13.805897086858998, 51.03947382084996]}, {"source": [1526, 2512], "target": [13.801451325417, 51.056040195115]}, {"source": [3446, 1037], "target": [13.810176551342, 51.060256512142985]}, {"source": [7181, 1768], "target": [13.827157616614999, 51.05825208143398]}, {"source": [8079, 4220], "target": [13.831320405006002, 51.051224930882995]}, {"source": [7076, 8075], "target": [13.826889395714, 51.04012228799499]}]}', 'missing', 10009482, 7912, NULL, '0103000020E61000000100000009000000497FFF4BF1972B407902EF51F08749403D6B00341FA02B409B4C6D8DEE8749404D23001430A02B4083438EFEEE874940441503C628AA2B4043926DA1EA8749405FA7003424AA2B40510602F50A874940E10F029C25AA2B407B473CC231854940CB8700DD20AA2B404E4D38AA09854940BC2F01D4E1972B407039402B0E854940497FFF4BF1972B407902EF51F0874940');
    INSERT INTO public.transformations VALUES (8968, '2017-01-24 18:04:35', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [141, 100], "target": [14.633178905627, 51.020024198702]}, {"source": [99, 8522], "target": [14.696518691953, 50.973790343052]}, {"source": [7189, 6870], "target": [14.745599564548, 51.016983154879]}, {"source": [7184, 6934], "target": [14.745985845448, 51.016635504728]}, {"source": [7919, 6659], "target": [14.750266591931, 51.021693102844]}, {"source": [7084, 4303], "target": [14.725179239728, 51.03060789138]}, {"source": [4126, 1238], "target": [14.675814966108, 51.033418446233]}, {"source": [4188, 586], "target": [14.671422801248, 51.037205648809]}, {"source": [3965, 1005], "target": [14.67284802314, 51.033846986587]}, {"source": [3451, 2330], "target": [14.678439965739, 51.024093486313]}, {"source": [964, 2459], "target": [14.657980127281, 51.011371311055]}, {"source": [219, 7977], "target": [14.693383770693, 50.977474298345]}, {"source": [468, 8147], "target": [14.696771018466, 50.977809513902]}, {"source": [4149, 7530], "target": [14.723987773013, 50.998797891012]}, {"source": [4502, 7736], "target": [14.728575049915, 50.999402205881]}, {"source": [7312, 6915], "target": [14.746965024045, 51.017329508545]}, {"source": [7202, 6734], "target": [14.744641015651, 51.017844674746]}, {"source": [7360, 6516], "target": [14.744402342623, 51.0197903878]}, {"source": [6034, 8212], "target": [14.745718872235, 51.004245195671]}, {"source": [6074, 8370], "target": [14.74729621243, 51.003482165835]}, {"source": [7134, 7351], "target": [14.748734518878, 51.014128465547]}, {"source": [8368, 8427], "target": [14.767784588111, 51.014248828239]}, {"source": [7225, 278], "target": [14.695556161076, 51.053369209564]}, {"source": [7686, 1719], "target": [14.710485527669, 51.047910220634]}, {"source": [4549, 1735], "target": [14.683354837654, 51.032563014898]}, {"source": [2925, 4936], "target": [14.693519097428, 51.007211841524]}, {"source": [3804, 8516], "target": [14.728349391651, 50.991483757522]}, {"source": [6941, 8513], "target": [14.756026435277, 51.006834846687]}, {"source": [5603, 8513], "target": [14.744126137815, 51.000233821334]}, {"source": [6009, 8511], "target": [14.747792445326, 51.002270946922]}, {"source": [2211, 8516], "target": [14.714497904724, 50.983799764164]}, {"source": [843, 8522], "target": [14.703131459123, 50.977495254883]}, {"source": [469, 8526], "target": [14.70000347355, 50.97576233599]}, {"source": [101, 7694], "target": [14.690254995519, 50.978341653636]}, {"source": [111, 5624], "target": [14.674412002826, 50.989915122771]}, {"source": [130, 1979], "target": [14.646911647803, 51.009994230935]}, {"source": [2768, 110], "target": [14.655867097594, 51.032828316013]}, {"source": [4399, 109], "target": [14.669534382431, 51.040542990954]}, {"source": [6031, 102], "target": [14.683616586587, 51.048485309369]}, {"source": [7790, 98], "target": [14.699245794977, 51.057296286307]}, {"source": [8558, 99], "target": [14.705860355246, 51.061058600186]}, {"source": [7355, 103], "target": [14.695361296572, 51.055134694568]}, {"source": [8545, 1523], "target": [14.716673614486, 51.053180008865]}, {"source": [8530, 3544], "target": [14.732049400731, 51.041953336139]}, {"source": [8523, 5515], "target": [14.746667819693, 51.031281533127]}, {"source": [8516, 7040], "target": [14.758419066287, 51.022704354357]}, {"source": [8518, 6257], "target": [14.752660579843, 51.026904982826]}, {"source": [8512, 8518], "target": [14.769741555155, 51.014432332068]}]}', 'valid', 10009405, 0, NULL, '0103000020DA1000000100000006000000D62E7A622E442D40A9944F35908249409BF1E47898642D4001309285A57C49407EDC469825862D405BEE1F964C814940D71CAEF91B8A2D40F1FEB6EED8814940C9A749A566692D404A45E0D9D0874940D62E7A622E442D40A9944F3590824940');
    INSERT INTO public.transformations VALUES (7912, '2016-06-29 14:51:34', 'user_2', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "tps", "gcps": [{"source": [3038, 3551], "target": [13.808341920376, 51.053044201955]}, {"source": [4998, 3553], "target": [13.817241489887, 51.053121759652]}, {"source": [4565, 3052], "target": [13.815058171749, 51.054389640982]}, {"source": [4810, 2511], "target": [13.816431462765, 51.056129549278]}, {"source": [766, 5503], "target": [13.798061013222, 51.047474882557]}, {"source": [4975, 8190], "target": [13.817291110754, 51.039806066529]}, {"source": [2962, 8280], "target": [13.808073699474, 51.039466231454]}, {"source": [2468, 8281], "target": [13.805897086859, 51.03947382085]}, {"source": [1526, 2512], "target": [13.801451325417, 51.056040195115]}, {"source": [3446, 1037], "target": [13.810176551342, 51.060256512143]}, {"source": [7181, 1768], "target": [13.827157616615, 51.058252081434]}, {"source": [8079, 4220], "target": [13.831320405006, 51.051224930883]}, {"source": [7076, 8075], "target": [13.826889395714, 51.040122287995]}]}', 'valid', 10009482, 0, NULL, '0103000020E61000000100000009000000305B004CF1972B408C5DEE51F08749403D6B00341FA02B40A1156D8DEE8749404D23001430A02B409C678DFEEE874940A8A5FFC528AA2B403DC96DA1EA87494078CBFF3324AA2B40636101F50A8749401358009C25AA2B40757E3CC231854940E4ABFFDC20AA2B404E4D38AA09854940D55300D4E1972B40514C412B0E854940305B004CF1972B408C5DEE51F0874940');
    INSERT INTO public.transformations VALUES (586, '2013-07-09 13:33:39', 'user_2', '{"source": "pixel", "target": "EPSG:4314", "gcps": [{"source": [591.0, 7160.0], "target": [13.6666660308838, 51.0]}, {"source": [587.0, 682.0], "target": [13.6666660308838, 51.1000022888184]}, {"source": [7393.0, 678.0], "target": [13.8333339691162, 51.1000022888184]}, {"source": [7395.0, 7149.0], "target": [13.8333339691162, 51.0]}]}', 'valid', 10001963, 0, NULL, '0103000020DA100000010000000500000038E50AA653552B401253A8C2CD8C4940904E14DA56552B40C4AB461DFF7F4940554E7A25A9AA2B401B09F8E200804940CA59675AACAA2B40DFE318FDCB8C494038E50AA653552B401253A8C2CD8C4940');
    INSERT INTO public.transformations VALUES (12021, '2018-05-18 12:15:55', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [591, 7160], "target": [13.666666029595, 50.999999999077]}, {"source": [587, 682], "target": [13.666666029528, 51.100002287839]}, {"source": [7393, 678], "target": [13.83333396768, 51.100002287798]}, {"source": [7395, 7149], "target": [13.833333967748, 50.999999999036]}, {"source": [3406, 3646], "target": [13.735497537138, 51.054225772972]}, {"source": [3630, 3924], "target": [13.74092965442, 51.049966997035]}, {"source": [3551, 3612], "target": [13.739073713592, 51.054746762352]}, {"source": [3911, 3010], "target": [13.747913493105, 51.06409741867]}, {"source": [6520, 3616], "target": [13.811833291042, 51.054611702269]}, {"source": [6114, 3058], "target": [13.801947732536, 51.063423027346]}, {"source": [5632, 5420], "target": [13.790161548678, 51.026747958975]}, {"source": [3459, 4900], "target": [13.736784708353, 51.034845527372]}, {"source": [2768, 3225], "target": [13.719939641684, 51.060734244405]}, {"source": [2750, 947], "target": [13.719455436774, 51.095988808105]}, {"source": [780, 6875], "target": [13.671194114344, 51.004336496106]}, {"source": [5046, 4287], "target": [13.775653824071, 51.04435875505]}, {"source": [7119, 6409], "target": [13.826655748725, 51.011473156931]}, {"source": [1857, 4324], "target": [13.697434385424, 51.043744535423]}, {"source": [4159, 2042], "target": [13.753986740724, 51.079049053639]}, {"source": [4388, 2170], "target": [13.759642819756, 51.077088279815]}, {"source": [4682, 5330], "target": [13.766854517874, 51.028221848711]}, {"source": [2962, 4897], "target": [13.724665919609, 51.034951063702]}, {"source": [3274, 6819], "target": [13.732236099243, 51.00517454581]}]}', 'valid', 10001963, 586, NULL, '0103000020DA100000010000000500000096DEFEA553552B40512DA6C2CD8C4940EFFCF84D55552B4073FAB7D8FF7F494069AFD75FAAAA2B40E18F0D6A00804940FAC99679ABAA2B40706BF29FCC8C494096DEFEA553552B40512DA6C2CD8C4940');
    INSERT INTO public.transformations VALUES (12042, '2018-05-23 13:19:50', 'user_1', '{"source": "pixel", "target": "EPSG:4326", "algorithm": "tps", "gcps": [{"source": [591, 7160], "target": [13.664944753983, 50.99876989452]}, {"source": [587, 682], "target": [13.664941043666, 51.098760873116]}, {"source": [7393, 678], "target": [13.831584310395, 51.098763349039]}, {"source": [7395, 7149], "target": [13.831588073778, 50.998772366996]}, {"source": [3406, 3646], "target": [13.73376407162, 51.05299055331]}, {"source": [3630, 3924], "target": [13.739195544592, 51.048732339538]}, {"source": [3551, 3612], "target": [13.737339699745, 51.053511536809]}, {"source": [3911, 3010], "target": [13.746177822442, 51.062861266887]}, {"source": [6520, 3616], "target": [13.810088523335, 51.053377574552]}, {"source": [6114, 3058], "target": [13.800204095554, 51.062187755837]}, {"source": [5632, 5420], "target": [13.78842102945, 51.025516658737]}, {"source": [3459, 4900], "target": [13.735051775616, 51.033612518392]}, {"source": [2768, 3225], "target": [13.718208234391, 51.059498058169]}, {"source": [2750, 947], "target": [13.717722785038, 51.094748627701]}, {"source": [780, 6875], "target": [13.669472009187, 51.003105967834]}, {"source": [5046, 4287], "target": [13.773914789792, 51.043125247567]}, {"source": [7119, 6409], "target": [13.824910410482, 51.010244127983]}, {"source": [1857, 4324], "target": [13.69570693929, 51.042509937633]}, {"source": [4159, 2042], "target": [13.752249612173, 51.077811301255]}, {"source": [4388, 2170], "target": [13.757904927795, 51.07585083321]}, {"source": [4682, 5330], "target": [13.765117387852, 51.026990035083]}, {"source": [2962, 4897], "target": [13.72293477446, 51.033717863213]}, {"source": [3274, 6819], "target": [13.730504944052, 51.003944824658]}, {"source": [3595, 3724], "target": [13.738403684799, 51.051782873865]}, {"source": [3729, 3714], "target": [13.741613435574, 51.051957076736]}, {"source": [2932, 1951], "target": [13.722140476153, 51.079205272004]}, {"source": [6411, 3941], "target": [13.807558957837, 51.048419320237]}, {"source": [5727, 3941], "target": [13.790767597917, 51.048419780125]}, {"source": [3151, 1385], "target": [13.727632664828, 51.08797423941]}, {"source": [5870, 2880], "target": [13.794225453417, 51.064812632266]}, {"source": [5760, 6429], "target": [13.791501243073, 51.009927550168]}, {"source": [6674, 1636], "target": [13.813946028925, 51.084052166975]}, {"source": [7193, 789], "target": [13.826812463755, 51.097093133208]}, {"source": [3562, 3200], "target": [13.737693508895, 51.059865792718]}, {"source": [6279, 4390], "target": [13.80418839649, 51.041525900981]}, {"source": [3635, 3511], "target": [13.739292837119, 51.05490325078]}, {"source": [4298, 2914], "target": [13.755797688282, 51.06424159007]}, {"source": [4891, 5948], "target": [13.770240653947, 51.017382879048]}]}', 'valid', 10001963, 12030, NULL, '0103000020E6100000010000000500000035B0198D71542B405A52E114A58C494038078DB173542B40C3C0DB89D77F4940C78F5B89C5A92B40EEB1EA2FD87F494085BAD024C6A92B40D8C0FB06A48C494035B0198D71542B405A52E114A58C4940');
    INSERT INTO public.transformations VALUES (12347, '2018-08-09 11:26:59', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [591, 7160], "target": [13.666666027017, 50.99999999723]}, {"source": [587, 682], "target": [13.666666026815, 51.100002285881]}, {"source": [7393, 678], "target": [13.833333964808, 51.100002285758]}, {"source": [7395, 7149], "target": [13.833333965012, 50.999999997108]}, {"source": [3406, 3646], "target": [13.735497534422, 51.054225771032]}, {"source": [3630, 3924], "target": [13.740929651704, 51.049966995097]}, {"source": [3551, 3612], "target": [13.739073710872, 51.054746760409]}, {"source": [3911, 3010], "target": [13.747913490365, 51.064097416712]}, {"source": [6520, 3616], "target": [13.811833288253, 51.054611700291]}, {"source": [6114, 3058], "target": [13.801947729744, 51.063423025363]}, {"source": [5632, 5420], "target": [13.790161545948, 51.026747957039]}, {"source": [3459, 4900], "target": [13.736784705663, 51.034845525453]}, {"source": [2768, 3225], "target": [13.719939638974, 51.060734242465]}, {"source": [2750, 947], "target": [13.719455434017, 51.095988806127]}, {"source": [780, 6875], "target": [13.671194111756, 51.004336494252]}, {"source": [5046, 4287], "target": [13.775653821331, 51.0443587531]}, {"source": [7119, 6409], "target": [13.826655745979, 51.011473154993]}, {"source": [1857, 4324], "target": [13.697434382758, 51.043744533514]}, {"source": [4159, 2042], "target": [13.753986737957, 51.079049051663]}, {"source": [4388, 2170], "target": [13.759642816986, 51.077088277837]}, {"source": [4682, 5330], "target": [13.766854515164, 51.028221846785]}, {"source": [2962, 4897], "target": [13.72466591693, 51.034951061788]}, {"source": [3274, 6819], "target": [13.732236096597, 51.005174543925]}, {"source": [3595, 3724], "target": [13.740137788729, 51.053017886174]}, {"source": [3729, 3714], "target": [13.743348020742, 51.053192061115]}, {"source": [2932, 1951], "target": [13.723873198254, 51.080443626943]}, {"source": [6411, 3941], "target": [13.80930316243, 51.049652923051]}, {"source": [5727, 3941], "target": [13.792509319751, 51.049653633418]}, {"source": [3151, 1385], "target": [13.729366527582, 51.089213504704]}, {"source": [5870, 2880], "target": [13.795968301908, 51.066048287795]}, {"source": [5760, 6429], "target": [13.793241631048, 51.011157039762]}, {"source": [6674, 1636], "target": [13.815692518459, 51.085289703856]}, {"source": [7193, 789], "target": [13.828561348891, 51.098331952453]}, {"source": [3562, 3200], "target": [13.73942780974, 51.061101729711]}, {"source": [6279, 4390], "target": [13.805931843907, 51.042758774578]}, {"source": [3635, 3511], "target": [13.741027189124, 51.056138602796]}, {"source": [4298, 2914], "target": [13.757534830956, 51.065477753087]}, {"source": [4891, 5948], "target": [13.771978179327, 51.018613528141]}, {"source": [7393, 4745], "target": [13.833329813093, 51.037071559231]}, {"source": [7394, 3062], "target": [13.833336583647, 51.063070396496]}, {"source": [3845, 3393], "target": [13.746365405068, 51.058092437802]}, {"source": [3991, 3390], "target": [13.750057163989, 51.058247656259]}, {"source": [4115, 4332], "target": [13.752977904818, 51.043698219962]}, {"source": [4590, 4625], "target": [13.764596767747, 51.039086108667]}, {"source": [4208, 2067], "target": [13.75526639954, 51.078586486588]}, {"source": [5967, 2220], "target": [13.79838920318, 51.076297091064]}, {"source": [5814, 3232], "target": [13.794572874923, 51.060595404846]}, {"source": [3004, 4837], "target": [13.725714090797, 51.035878483759]}, {"source": [3030, 5150], "target": [13.726322928757, 51.031030411236]}, {"source": [891, 1637], "target": [13.673959005873, 51.085244320156]}, {"source": [805, 4553], "target": [13.671813395337, 51.040240046183]}]}', 'valid', 10001963, 12047, NULL, '0103000020DA10000001000000050000002D26D8AD55552B4039E65EDFCC8C494079A7E24D55552B40E41CB4D8FF7F49400198E3BBAAAA2B40A8B9190D008049401A5A288FAAAA2B40BE3235E1CC8C49402D26D8AD55552B4039E65EDFCC8C4940');
    INSERT INTO public.transformations VALUES (12030, '2018-05-22 12:08:58', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [591, 7160], "target": [13.666666028306, 50.999999998154]}, {"source": [587, 682], "target": [13.666666028172, 51.10000228686]}, {"source": [7393, 678], "target": [13.833333966244, 51.100002286778]}, {"source": [7395, 7149], "target": [13.83333396638, 50.999999998072]}, {"source": [3406, 3646], "target": [13.73549753578, 51.054225772002]}, {"source": [3630, 3924], "target": [13.740929653062, 51.049966996066]}, {"source": [3551, 3612], "target": [13.739073712232, 51.054746761381]}, {"source": [3911, 3010], "target": [13.747913491735, 51.064097417691]}, {"source": [6520, 3616], "target": [13.811833289647, 51.05461170128]}, {"source": [6114, 3058], "target": [13.80194773114, 51.063423026354]}, {"source": [5632, 5420], "target": [13.790161547313, 51.026747958007]}, {"source": [3459, 4900], "target": [13.736784707008, 51.034845526412]}, {"source": [2768, 3225], "target": [13.719939640329, 51.060734243435]}, {"source": [2750, 947], "target": [13.719455435395, 51.095988807116]}, {"source": [780, 6875], "target": [13.67119411305, 51.004336495179]}, {"source": [5046, 4287], "target": [13.775653822701, 51.044358754075]}, {"source": [7119, 6409], "target": [13.826655747352, 51.011473155962]}, {"source": [1857, 4324], "target": [13.697434384091, 51.043744534468]}, {"source": [4159, 2042], "target": [13.75398673934, 51.079049052651]}, {"source": [4388, 2170], "target": [13.759642818371, 51.077088278826]}, {"source": [4682, 5330], "target": [13.766854516519, 51.028221847748]}, {"source": [2962, 4897], "target": [13.724665918269, 51.034951062745]}, {"source": [3274, 6819], "target": [13.73223609792, 51.005174544868]}, {"source": [3595, 3724], "target": [13.740137790089, 51.053017887145]}, {"source": [3729, 3714], "target": [13.743348022103, 51.053192062086]}, {"source": [2932, 1951], "target": [13.723873199624, 51.080443627925]}, {"source": [6411, 3941], "target": [13.80930316382, 51.049652924037]}, {"source": [5727, 3941], "target": [13.792509321133, 51.0496536344]}, {"source": [3151, 1385], "target": [13.729366528961, 51.089213505692]}, {"source": [5870, 2880], "target": [13.795968303303, 51.066048288786]}, {"source": [5760, 6429], "target": [13.793241632404, 51.011157040723]}, {"source": [6674, 1636], "target": [13.815692519877, 51.085289704863]}, {"source": [7193, 789], "target": [13.828561350324, 51.098331953471]}, {"source": [3562, 3200], "target": [13.739427811104, 51.061101730686]}, {"source": [6279, 4390], "target": [13.805931845291, 51.042758775559]}, {"source": [3635, 3511], "target": [13.741027190486, 51.056138603769]}, {"source": [4298, 2914], "target": [13.757534832332, 51.065477754069]}]}', 'valid', 10001963, 12021, NULL, '0103000020DA1000000100000005000000F4D7F2A553552B408F07A4C2CD8C494034D2ED4D55552B40AC0BB6D8FF7F4940C7A8CB5FAAAA2B401F6A0B6A0080494058C38A79ABAA2B40AF45F09FCC8C4940F4D7F2A553552B408F07A4C2CD8C4940');
    INSERT INTO public.transformations VALUES (7926, '2016-07-04 10:54:15', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [4889, 4752], "target": [13.736074026403, 51.055140229098]}, {"source": [5549, 5002], "target": [13.740504828265, 51.049994445396]}, {"source": [7801, 4766], "target": [13.764599584292, 51.039081891669]}, {"source": [3508, 5076], "target": [13.719875988333, 51.060668338268]}, {"source": [523, 6779], "target": [13.676179227324, 51.06620209387]}, {"source": [1090, 2738], "target": [13.716912736301, 51.088199258538]}, {"source": [3838, 2775], "target": [13.743201706716, 51.072997728055]}, {"source": [4814, 3198], "target": [13.748968679097, 51.065113244387]}, {"source": [7891, 5262], "target": [13.760964517929, 51.035448474345]}, {"source": [4408, 5925], "target": [13.721273242016, 51.050372479172]}, {"source": [5592, 5254], "target": [13.73864034931, 51.048173141454]}, {"source": [6793, 994], "target": [13.787341122543, 51.068176155044]}, {"source": [6783, 4942], "target": [13.753139663043, 51.043626030437]}, {"source": [1888, 3509], "target": [13.71794519606, 51.07899826238]}, {"source": [1854, 6761], "target": [13.689412243058, 51.058696131086]}, {"source": [5101, 4606], "target": [13.739678769716, 51.054921812517]}, {"source": [5666, 2452], "target": [13.763692504025, 51.065317432595]}]}', 'valid', 10009466, 0, NULL, '0103000020DA1000000100000009000000CF9559E41D752B40CB5902E6868D4940BA9E9E7675602B40B6355DE8B5894940E6278389D9542B40AC9887599A874940ED44AC725F7A2B4044C81EFD6D82494016438A61CD952B400BD16267718749404BD9E6E124992B40102F8EDD0C884940E934DD7B50992B408FBA4FEE1488494079F93B6ABC9A2B40704A515358884940CF9559E41D752B40CB5902E6868D4940');
    INSERT INTO public.transformations VALUES (19, '2021-10-04 17:27:22.331319', 'user_1', '{"source": "pixel", "target": "EPSG:4314", "algorithm": "tps", "gcps": [{"source": [6700, 998], "target": [14.809598142072, 50.897193140898]}, {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]}, {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]}, {"source": [6969, 3160], "target": [14.816612768409, 50.863606051111]}, {"source": [1907, 1301], "target": [14.690521818997, 50.891860483128]}, {"source": [4180, 4396], "target": [14.747856876595, 50.843955582846]}, {"source": [5070, 5489], "target": [14.769772087663, 50.827125251053]}, {"source": [6933, 7171], "target": [14.816342007402, 50.801483295161]}, {"source": [3325, 7152], "target": [14.727274235239, 50.801026963158]}, {"source": [1509, 6622], "target": [14.681454720195, 50.808715847718]}]}', 'missing', 10001556, 11823, NULL, '0103000020DA100000010000000B000000CEAA2A8FC9532D4080CEE1B02D734940F5511DDDCE522D4049E3C4155F664940D69B832D97872D403289D3796F6649402EF4569732882D40F00D71EB6F6649402B1B36C742882D40DCBCA18B2E6549407F7197679F902D40551E423431654940F52FEBF388902D40B475242272664940ABE732A2A5A82D404BAEEBE2796649401080181E84A82D404288914939734940ABB411C483A82D404288914939734940CEAA2A8FC9532D4080CEE1B02D734940');


    --
    -- Name: georef_maps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
    --

    SELECT pg_catalog.setval('public.georef_maps_id_seq', 1, false);


    --
    -- Name: jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
    --

    SELECT pg_catalog.setval('public.jobs_id_seq', 28, true);


    --
    -- Name: original_maps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
    --

    SELECT pg_catalog.setval('public.original_maps_id_seq', 1, false);


    --
    -- Name: transformations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
    --

    SELECT pg_catalog.setval('public.transformations_id_seq', 42, true);


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

EOSQL
# SQL database

To store the data that will be retrieved from PubMed, a postgres database will be used. The code in this file represents the CREATE scripts for the database. For the data pipeline to work, it is crucial to create a database user that can be used by the python program, as well as the different tables to store the data. The structure of the tables must match the functions of the webcrawler! It is highly recommended to use the common wizards and admin tools to set up the database. However, the code below can provide some hints when making decisions on the database configuration.

The general approach favors speed over data integrity because we expect already well-ordered and clean data from PubMed (which we will get, trust me!). In this regard, two further notes:
- Don't create the indexes after all crawling was done. Otherwise, the database has to ongoingly update the index during the crawling procedure which can block resources and slow everything down. 
- Similarly, primary and foreign keys with their relationships and events can be created after the data was entered into the database. 
- Avoid the date type used by postgres. The integration with python/psycopg2 is not straightforward and there are some invalid dates in PubMed. Making this to work is not worth the efforts because the transformation can also be done afterwards. Also keep in mind that you won't work with months or even days in most bibliometric analayses, because this information is not reliable. 


## Initialization of the database

Creation of the database "postgres"
```sql
-- Database: postgres

-- DROP DATABASE IF EXISTS postgres;

CREATE DATABASE postgres
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'German_Germany.1252'
    LC_CTYPE = 'German_Germany.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE postgres
    IS 'default administrative connection database';
```

Creation of the schema "public"
```sql
-- SCHEMA: public

-- DROP SCHEMA IF EXISTS public ;

CREATE SCHEMA IF NOT EXISTS public
    AUTHORIZATION postgres;

COMMENT ON SCHEMA public
    IS 'standard public schema';

GRANT ALL ON SCHEMA public TO PUBLIC;

GRANT ALL ON SCHEMA public TO postgres;
```

Lastly, a user is created that will be used by the python program to write data into the database. Configure the ["databasecredentials.py"](databasecredentials.py) accordingly!
```sql
-- Role: pythonboy
-- DROP ROLE IF EXISTS pythonboy;

CREATE ROLE pythonboy WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION
  ENCRYPTED PASSWORD '<placeholder>';

GRANT pg_read_all_data, pg_write_all_data TO pythonboy;
```

## Tables
It is crucial that the structure of the tables and their names matches the function of the parsers, otherwise psycopg2 will fail to write data. **It is highly recommended to build the indexes after all data was included into the database. Otherwise, the database has to update the index during the crawling procedure which slows everything down.**

Table for items
```sql
-- Table: public.raw_items

-- DROP TABLE IF EXISTS public.raw_items;

CREATE TABLE IF NOT EXISTS public.raw_items
(
    pmid text COLLATE pg_catalog."default" NOT NULL,
    doi text COLLATE pg_catalog."default",
    pubmodel text COLLATE pg_catalog."default",
    crawlingset integer NOT NULL,
    doi_pubmodel text COLLATE pg_catalog."default",
    title text COLLATE pg_catalog."default",
    abstract text COLLATE pg_catalog."default",
    pmid_version text COLLATE pg_catalog."default" NOT NULL,
    j_title_abbrev text COLLATE pg_catalog."default",
    j_nlm_id_unique text COLLATE pg_catalog."default",
    pk_items integer NOT NULL
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.raw_items
    OWNER to postgres;
-- Index: idx_items_pkitems

-- DROP INDEX IF EXISTS public.idx_items_pkitems;

CREATE INDEX IF NOT EXISTS idx_items_pkitems
    ON public.raw_items USING btree
    (pk_items ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_pmid

-- DROP INDEX IF EXISTS public.idx_pmid;

CREATE INDEX IF NOT EXISTS idx_pmid
    ON public.raw_items USING btree
    (pmid COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
```

Table for the references of the items (bibliography)
```sql
-- Table: public.raw_bibliography

-- DROP TABLE IF EXISTS public.raw_bibliography;

CREATE TABLE IF NOT EXISTS public.raw_bibliography
(
    cited_pmid text COLLATE pg_catalog."default",
    reference_string text COLLATE pg_catalog."default",
    fk_items integer
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.raw_bibliography
    OWNER to postgres;
-- Index: idx_biblio_fkitems

-- DROP INDEX IF EXISTS public.idx_biblio_fkitems;

CREATE INDEX IF NOT EXISTS idx_biblio_fkitems
    ON public.raw_bibliography USING btree
    (fk_items ASC NULLS LAST)
    TABLESPACE pg_default;
```

Table for the mesh keywords
```sql
-- Table: public.raw_meshinfo

-- DROP TABLE IF EXISTS public.raw_meshinfo;

CREATE TABLE IF NOT EXISTS public.raw_meshinfo
(
    mesh_heading text COLLATE pg_catalog."default",
    mesh_descriptor text COLLATE pg_catalog."default",
    maj_heading boolean,
    maj_descriptor boolean,
    corona boolean,
    fk_items integer
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.raw_meshinfo
    OWNER to postgres;
-- Index: idx_mesh_fkitems

-- DROP INDEX IF EXISTS public.idx_mesh_fkitems;

CREATE INDEX IF NOT EXISTS idx_mesh_fkitems
    ON public.raw_meshinfo USING btree
    (fk_items ASC NULLS LAST)
    TABLESPACE pg_default;
```

Table for the publication types
```sql
-- Table: public.raw_ptypes

-- DROP TABLE IF EXISTS public.raw_ptypes;

CREATE TABLE IF NOT EXISTS public.raw_ptypes
(
    ptype text COLLATE pg_catalog."default",
    fk_items integer
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.raw_ptypes
    OWNER to postgres;
-- Index: idx_ptype_fkitems

-- DROP INDEX IF EXISTS public.idx_ptype_fkitems;

CREATE INDEX IF NOT EXISTS idx_ptype_fkitems
    ON public.raw_ptypes USING btree
    (fk_items ASC NULLS LAST)
    TABLESPACE pg_default;
```

Table for publication dates
```sql
-- Table: public.raw_pubdates

-- DROP TABLE IF EXISTS public.raw_pubdates;

CREATE TABLE IF NOT EXISTS public.raw_pubdates
(
    datetype text COLLATE pg_catalog."default",
    d_full date,
    d_year text COLLATE pg_catalog."default",
    d_month text COLLATE pg_catalog."default",
    d_day text COLLATE pg_catalog."default",
    d_season text COLLATE pg_catalog."default",
    fk_items integer
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.raw_pubdates
    OWNER to postgres;
-- Index: idx_dates_fkitems

-- DROP INDEX IF EXISTS public.idx_dates_fkitems;

CREATE INDEX IF NOT EXISTS idx_dates_fkitems
    ON public.raw_pubdates USING btree
    (fk_items ASC NULLS LAST)
    TABLESPACE pg_default;
```


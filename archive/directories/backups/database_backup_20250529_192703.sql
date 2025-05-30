--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9
-- Dumped by pg_dump version 16.3

-- Started on 2025-05-29 19:27:03 UTC

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

DROP DATABASE neondb;
--
-- TOC entry 3655 (class 1262 OID 16389)
-- Name: neondb; Type: DATABASE; Schema: -; Owner: neondb_owner
--

CREATE DATABASE neondb WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'C.UTF-8';


ALTER DATABASE neondb OWNER TO neondb_owner;

\connect neondb

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
-- TOC entry 5 (class 2615 OID 65562)
-- Name: public; Type: SCHEMA; Schema: -; Owner: neondb_owner
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO neondb_owner;

--
-- TOC entry 3657 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: neondb_owner
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 242 (class 1259 OID 98315)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO neondb_owner;

--
-- TOC entry 224 (class 1259 OID 65629)
-- Name: audit_entries; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.audit_entries (
    id integer NOT NULL,
    "timestamp" timestamp without time zone,
    event_type character varying(50) NOT NULL,
    severity character varying(20),
    resource_type character varying(50),
    resource_id character varying(50),
    operation_id integer,
    description text NOT NULL,
    previous_state text,
    new_state text,
    user_id integer,
    username character varying(100),
    ip_address character varying(50),
    additional_data text,
    correlation_id character varying(50)
);


ALTER TABLE public.audit_entries OWNER TO neondb_owner;

--
-- TOC entry 223 (class 1259 OID 65628)
-- Name: audit_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.audit_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_entries_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3659 (class 0 OID 0)
-- Dependencies: 223
-- Name: audit_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.audit_entries_id_seq OWNED BY public.audit_entries.id;


--
-- TOC entry 250 (class 1259 OID 122910)
-- Name: audit_entry; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.audit_entry (
    id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id character varying(50),
    operation_id integer,
    description text NOT NULL,
    previous_state json,
    new_state json,
    severity character varying(20),
    user_id character varying(50),
    username character varying(100),
    ip_address character varying(50),
    created_at timestamp without time zone,
    correlation_id character varying(36)
);


ALTER TABLE public.audit_entry OWNER TO neondb_owner;

--
-- TOC entry 249 (class 1259 OID 122909)
-- Name: audit_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.audit_entry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_entry_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3660 (class 0 OID 0)
-- Dependencies: 249
-- Name: audit_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.audit_entry_id_seq OWNED BY public.audit_entry.id;


--
-- TOC entry 267 (class 1259 OID 147456)
-- Name: compliance_audit_logs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.compliance_audit_logs (
    id uuid NOT NULL,
    operation_id character varying(255) NOT NULL,
    record_type character varying(100) NOT NULL,
    record_id character varying(255) NOT NULL,
    operation_type character varying(100) NOT NULL,
    source_system character varying(100) NOT NULL,
    ai_model_version character varying(100),
    confidence_score double precision,
    user_id character varying(255),
    "timestamp" timestamp without time zone,
    data_hash character varying(64),
    change_summary text,
    compliance_flags text,
    review_required boolean,
    reviewed_by character varying(255),
    reviewed_at timestamp without time zone,
    review_notes text
);


ALTER TABLE public.compliance_audit_logs OWNER TO neondb_owner;

--
-- TOC entry 256 (class 1259 OID 131116)
-- Name: counties; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.counties (
    id integer NOT NULL,
    county_id character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    state character varying(32),
    config_path character varying(256),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.counties OWNER TO neondb_owner;

--
-- TOC entry 255 (class 1259 OID 131115)
-- Name: counties_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.counties_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.counties_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3661 (class 0 OID 0)
-- Dependencies: 255
-- Name: counties_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.counties_id_seq OWNED BY public.counties.id;


--
-- TOC entry 246 (class 1259 OID 122890)
-- Name: gis_export_job; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.gis_export_job (
    id integer NOT NULL,
    job_id character varying(36),
    county_id character varying(50) NOT NULL,
    username character varying(100) NOT NULL,
    export_format character varying(20) NOT NULL,
    area_of_interest json NOT NULL,
    layers json NOT NULL,
    status character varying(20),
    created_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    download_url character varying(500),
    result_file_location character varying(500),
    result_file_size_kb integer,
    result_record_count integer,
    message character varying(500),
    updated_at timestamp without time zone
);


ALTER TABLE public.gis_export_job OWNER TO neondb_owner;

--
-- TOC entry 245 (class 1259 OID 122889)
-- Name: gis_export_job_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.gis_export_job_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gis_export_job_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3662 (class 0 OID 0)
-- Dependencies: 245
-- Name: gis_export_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.gis_export_job_id_seq OWNED BY public.gis_export_job.id;


--
-- TOC entry 258 (class 1259 OID 131125)
-- Name: gis_export_jobs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.gis_export_jobs (
    id integer NOT NULL,
    job_id character varying(64) NOT NULL,
    county_id character varying(64),
    user_id integer,
    username character varying(64),
    export_format character varying(32) NOT NULL,
    area_of_interest json,
    layers json,
    parameters json,
    status character varying(32),
    message text,
    file_path character varying(256),
    file_size integer,
    download_url character varying(256),
    created_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone
);


ALTER TABLE public.gis_export_jobs OWNER TO neondb_owner;

--
-- TOC entry 257 (class 1259 OID 131124)
-- Name: gis_export_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.gis_export_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gis_export_jobs_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3663 (class 0 OID 0)
-- Dependencies: 257
-- Name: gis_export_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.gis_export_jobs_id_seq OWNED BY public.gis_export_jobs.id;


--
-- TOC entry 237 (class 1259 OID 81967)
-- Name: import_jobs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.import_jobs (
    id integer NOT NULL,
    source_system_id integer NOT NULL,
    job_type character varying(50) NOT NULL,
    status character varying(30),
    total_records integer,
    processed_records integer,
    successful_records integer,
    failed_records integer,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    estimated_completion_time timestamp without time zone,
    job_parameters json,
    result_summary text,
    error_log text,
    created_at timestamp without time zone,
    created_by character varying(100)
);


ALTER TABLE public.import_jobs OWNER TO neondb_owner;

--
-- TOC entry 236 (class 1259 OID 81966)
-- Name: import_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.import_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.import_jobs_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3664 (class 0 OID 0)
-- Dependencies: 236
-- Name: import_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.import_jobs_id_seq OWNED BY public.import_jobs.id;


--
-- TOC entry 241 (class 1259 OID 90112)
-- Name: market_analysis_jobs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.market_analysis_jobs (
    job_id character varying(36) NOT NULL,
    analysis_type character varying(50) NOT NULL,
    county_id character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    message text,
    parameters_json json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    result_summary_json json,
    result_data_location character varying(255)
);


ALTER TABLE public.market_analysis_jobs OWNER TO neondb_owner;

--
-- TOC entry 3665 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.job_id; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.job_id IS 'Unique ID for the market analysis job';


--
-- TOC entry 3666 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.analysis_type; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.analysis_type IS 'Type of market analysis (e.g., trend_analysis, comparable_market_area)';


--
-- TOC entry 3667 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.county_id; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.county_id IS 'County ID for the analysis';


--
-- TOC entry 3668 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.status; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.status IS 'e.g., PENDING, RUNNING, COMPLETED, FAILED';


--
-- TOC entry 3669 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.message; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.message IS 'Status message or error details';


--
-- TOC entry 3670 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.parameters_json; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.parameters_json IS 'JSON object storing parameters for the analysis (e.g., date ranges, property types)';


--
-- TOC entry 3671 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.result_summary_json; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.result_summary_json IS 'Summary of the analysis results';


--
-- TOC entry 3672 (class 0 OID 0)
-- Dependencies: 241
-- Name: COLUMN market_analysis_jobs.result_data_location; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.market_analysis_jobs.result_data_location IS 'Location/identifier for more detailed result data (e.g., S3 path, table name)';


--
-- TOC entry 228 (class 1259 OID 73729)
-- Name: onboarding_event; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.onboarding_event (
    id integer NOT NULL,
    user_onboarding_id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    step_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    event_data json
);


ALTER TABLE public.onboarding_event OWNER TO neondb_owner;

--
-- TOC entry 227 (class 1259 OID 73728)
-- Name: onboarding_event_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.onboarding_event_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.onboarding_event_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3673 (class 0 OID 0)
-- Dependencies: 227
-- Name: onboarding_event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.onboarding_event_id_seq OWNED BY public.onboarding_event.id;


--
-- TOC entry 220 (class 1259 OID 65601)
-- Name: onboarding_events; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.onboarding_events (
    id integer NOT NULL,
    user_id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    step_number integer,
    event_data text,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.onboarding_events OWNER TO neondb_owner;

--
-- TOC entry 219 (class 1259 OID 65600)
-- Name: onboarding_events_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.onboarding_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.onboarding_events_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3674 (class 0 OID 0)
-- Dependencies: 219
-- Name: onboarding_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.onboarding_events_id_seq OWNED BY public.onboarding_events.id;


--
-- TOC entry 229 (class 1259 OID 81920)
-- Name: properties_operational; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.properties_operational (
    property_id character varying(50) NOT NULL,
    county_id character varying(20) NOT NULL,
    parcel_number character varying(50) NOT NULL,
    address_street character varying(100) NOT NULL,
    address_city character varying(50) NOT NULL,
    address_state character varying(2) NOT NULL,
    address_zip character varying(10) NOT NULL,
    property_type character varying(30) NOT NULL,
    land_area_sqft double precision,
    building_area_sqft double precision,
    year_built integer,
    bedrooms integer,
    bathrooms double precision,
    last_sale_date timestamp without time zone,
    last_sale_price double precision,
    current_market_value double precision,
    assessed_value double precision,
    assessment_year integer,
    tax_district character varying(50),
    millage_rate double precision,
    tax_amount double precision,
    owner_name character varying(100),
    owner_type character varying(30),
    latitude double precision,
    longitude double precision,
    legal_description text,
    is_exempt boolean,
    exemption_type character varying(50),
    is_historical boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    last_sync_id integer,
    data_source character varying(50),
    extended_attributes json
);


ALTER TABLE public.properties_operational OWNER TO neondb_owner;

--
-- TOC entry 235 (class 1259 OID 81953)
-- Name: property_improvements; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.property_improvements (
    id integer NOT NULL,
    property_id character varying(50) NOT NULL,
    improvement_type character varying(50) NOT NULL,
    description text NOT NULL,
    year_completed integer,
    area_added_sqft double precision,
    cost double precision,
    value_added double precision,
    permit_number character varying(50),
    permit_date timestamp without time zone,
    permit_status character varying(30),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    data_source character varying(50)
);


ALTER TABLE public.property_improvements OWNER TO neondb_owner;

--
-- TOC entry 234 (class 1259 OID 81952)
-- Name: property_improvements_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.property_improvements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.property_improvements_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3675 (class 0 OID 0)
-- Dependencies: 234
-- Name: property_improvements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.property_improvements_id_seq OWNED BY public.property_improvements.id;


--
-- TOC entry 239 (class 1259 OID 81993)
-- Name: property_operational; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.property_operational (
    property_id character varying(50) NOT NULL,
    county_id character varying(20) NOT NULL,
    parcel_number character varying(50) NOT NULL,
    address_street character varying(100) NOT NULL,
    address_city character varying(50) NOT NULL,
    address_state character varying(2) NOT NULL,
    address_zip character varying(10) NOT NULL,
    property_type character varying(30) NOT NULL,
    land_area_sqft double precision,
    building_area_sqft double precision,
    year_built integer,
    bedrooms integer,
    bathrooms double precision,
    last_sale_date timestamp without time zone,
    last_sale_price double precision,
    current_market_value double precision,
    assessed_value double precision,
    assessment_year integer,
    tax_district character varying(50),
    millage_rate double precision,
    tax_amount double precision,
    owner_name character varying(100),
    owner_type character varying(30),
    latitude double precision,
    longitude double precision,
    legal_description text,
    is_exempt boolean,
    exemption_type character varying(50),
    is_historical boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    last_sync_id integer,
    data_source character varying(50),
    extended_attributes json
);


ALTER TABLE public.property_operational OWNER TO neondb_owner;

--
-- TOC entry 233 (class 1259 OID 81939)
-- Name: property_valuations; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.property_valuations (
    id integer NOT NULL,
    property_id character varying(50) NOT NULL,
    valuation_date timestamp without time zone,
    valuation_amount double precision NOT NULL,
    valuation_method character varying(50) NOT NULL,
    valuation_type character varying(30) NOT NULL,
    valuation_year integer NOT NULL,
    confidence_score double precision,
    margin_of_error double precision,
    comparables_used json,
    adjustments json,
    notes text,
    is_final boolean,
    approved_by character varying(100),
    approved_at timestamp without time zone,
    created_at timestamp without time zone,
    created_by character varying(100),
    sync_operation_id integer
);


ALTER TABLE public.property_valuations OWNER TO neondb_owner;

--
-- TOC entry 232 (class 1259 OID 81938)
-- Name: property_valuations_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.property_valuations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.property_valuations_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3676 (class 0 OID 0)
-- Dependencies: 232
-- Name: property_valuations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.property_valuations_id_seq OWNED BY public.property_valuations.id;


--
-- TOC entry 264 (class 1259 OID 139282)
-- Name: rbac_audit_log; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.rbac_audit_log (
    id integer NOT NULL,
    action_type character varying(32) NOT NULL,
    target_user_id integer,
    target_username character varying(64),
    admin_user_id integer,
    admin_username character varying(64),
    details jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ip_address inet
);


ALTER TABLE public.rbac_audit_log OWNER TO neondb_owner;

--
-- TOC entry 263 (class 1259 OID 139281)
-- Name: rbac_audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.rbac_audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rbac_audit_log_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3677 (class 0 OID 0)
-- Dependencies: 263
-- Name: rbac_audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.rbac_audit_log_id_seq OWNED BY public.rbac_audit_log.id;


--
-- TOC entry 266 (class 1259 OID 139292)
-- Name: rbac_sessions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.rbac_sessions (
    id integer NOT NULL,
    user_id integer,
    session_token character varying(255) NOT NULL,
    jwt_token text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    ip_address inet,
    user_agent text
);


ALTER TABLE public.rbac_sessions OWNER TO neondb_owner;

--
-- TOC entry 265 (class 1259 OID 139291)
-- Name: rbac_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.rbac_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rbac_sessions_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3678 (class 0 OID 0)
-- Dependencies: 265
-- Name: rbac_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.rbac_sessions_id_seq OWNED BY public.rbac_sessions.id;


--
-- TOC entry 262 (class 1259 OID 139265)
-- Name: rbac_users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.rbac_users (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(256),
    role character varying(32) DEFAULT 'viewer'::character varying NOT NULL,
    county_id character varying(64),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone
);


ALTER TABLE public.rbac_users OWNER TO neondb_owner;

--
-- TOC entry 261 (class 1259 OID 139264)
-- Name: rbac_users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.rbac_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rbac_users_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3679 (class 0 OID 0)
-- Dependencies: 261
-- Name: rbac_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.rbac_users_id_seq OWNED BY public.rbac_users.id;


--
-- TOC entry 240 (class 1259 OID 82002)
-- Name: report_job; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.report_job (
    report_id character varying(36) NOT NULL,
    report_type character varying(50) NOT NULL,
    county_id character varying(20) NOT NULL,
    status character varying(30) NOT NULL,
    message text,
    parameters_json json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    result_location character varying(255),
    result_metadata_json json
);


ALTER TABLE public.report_job OWNER TO neondb_owner;

--
-- TOC entry 3680 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.report_type; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.report_type IS 'Type of report being generated (e.g., sales_ratio_study, assessment_roll)';


--
-- TOC entry 3681 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.county_id; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.county_id IS 'County ID for which the report is generated';


--
-- TOC entry 3682 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.status; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.status IS 'Report job status: PENDING, RUNNING, COMPLETED, FAILED';


--
-- TOC entry 3683 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.message; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.message IS 'Status message or error details';


--
-- TOC entry 3684 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.parameters_json; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.parameters_json IS 'JSON object storing the parameters used for report generation';


--
-- TOC entry 3685 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.created_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.created_at IS 'Timestamp when the job was created';


--
-- TOC entry 3686 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.updated_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.updated_at IS 'Timestamp of the last status update';


--
-- TOC entry 3687 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.started_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.started_at IS 'Timestamp when report generation started';


--
-- TOC entry 3688 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.completed_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.completed_at IS 'Timestamp when report generation completed or failed';


--
-- TOC entry 3689 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.result_location; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.result_location IS 'Location/identifier of the generated report (e.g., S3 path, URL)';


--
-- TOC entry 3690 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN report_job.result_metadata_json; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_job.result_metadata_json IS 'Optional metadata about the report result (e.g., file size, page count)';


--
-- TOC entry 238 (class 1259 OID 81981)
-- Name: report_jobs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.report_jobs (
    report_id character varying(36) NOT NULL,
    report_type character varying(50) NOT NULL,
    county_id character varying(20) NOT NULL,
    status character varying(30) NOT NULL,
    message text,
    parameters_json json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    result_location character varying(255),
    result_metadata_json json
);


ALTER TABLE public.report_jobs OWNER TO neondb_owner;

--
-- TOC entry 3691 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.report_type; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.report_type IS 'Type of report being generated (e.g., sales_ratio_study, assessment_roll)';


--
-- TOC entry 3692 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.county_id; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.county_id IS 'County ID for which the report is generated';


--
-- TOC entry 3693 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.status; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.status IS 'Report job status: PENDING, RUNNING, COMPLETED, FAILED';


--
-- TOC entry 3694 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.message; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.message IS 'Status message or error details';


--
-- TOC entry 3695 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.parameters_json; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.parameters_json IS 'JSON object storing the parameters used for report generation';


--
-- TOC entry 3696 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.created_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.created_at IS 'Timestamp when the job was created';


--
-- TOC entry 3697 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.updated_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.updated_at IS 'Timestamp of the last status update';


--
-- TOC entry 3698 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.started_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.started_at IS 'Timestamp when report generation started';


--
-- TOC entry 3699 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.completed_at; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.completed_at IS 'Timestamp when report generation completed or failed';


--
-- TOC entry 3700 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.result_location; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.result_location IS 'Location/identifier of the generated report (e.g., S3 path, URL)';


--
-- TOC entry 3701 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN report_jobs.result_metadata_json; Type: COMMENT; Schema: public; Owner: neondb_owner
--

COMMENT ON COLUMN public.report_jobs.result_metadata_json IS 'Optional metadata about the report result (e.g., file size, page count)';


--
-- TOC entry 260 (class 1259 OID 131146)
-- Name: sync_jobs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sync_jobs (
    id integer NOT NULL,
    job_id character varying(64) NOT NULL,
    county_id character varying(64),
    user_id integer,
    username character varying(64),
    data_types json,
    source_system character varying(64),
    target_system character varying(64),
    parameters json,
    status character varying(32),
    message text,
    stats json,
    created_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    duration_seconds double precision
);


ALTER TABLE public.sync_jobs OWNER TO neondb_owner;

--
-- TOC entry 259 (class 1259 OID 131145)
-- Name: sync_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sync_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_jobs_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3702 (class 0 OID 0)
-- Dependencies: 259
-- Name: sync_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sync_jobs_id_seq OWNED BY public.sync_jobs.id;


--
-- TOC entry 252 (class 1259 OID 122919)
-- Name: sync_operation; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sync_operation (
    id integer NOT NULL,
    sync_pair_id integer,
    status character varying(20),
    created_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    records_processed integer,
    records_created integer,
    records_updated integer,
    records_deleted integer,
    errors integer,
    error_details json,
    user_id character varying(50)
);


ALTER TABLE public.sync_operation OWNER TO neondb_owner;

--
-- TOC entry 251 (class 1259 OID 122918)
-- Name: sync_operation_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sync_operation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_operation_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3703 (class 0 OID 0)
-- Dependencies: 251
-- Name: sync_operation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sync_operation_id_seq OWNED BY public.sync_operation.id;


--
-- TOC entry 226 (class 1259 OID 65643)
-- Name: sync_operations; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sync_operations (
    id integer NOT NULL,
    sync_pair_id integer NOT NULL,
    status character varying(50),
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    items_processed integer,
    items_succeeded integer,
    items_failed integer,
    log text,
    result_summary text,
    error_message text,
    initiated_by_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.sync_operations OWNER TO neondb_owner;

--
-- TOC entry 225 (class 1259 OID 65642)
-- Name: sync_operations_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sync_operations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_operations_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3704 (class 0 OID 0)
-- Dependencies: 225
-- Name: sync_operations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sync_operations_id_seq OWNED BY public.sync_operations.id;


--
-- TOC entry 244 (class 1259 OID 122881)
-- Name: sync_pair; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sync_pair (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    source_system character varying(50) NOT NULL,
    target_system character varying(50) NOT NULL,
    active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    county_id character varying(50) NOT NULL,
    config json
);


ALTER TABLE public.sync_pair OWNER TO neondb_owner;

--
-- TOC entry 243 (class 1259 OID 122880)
-- Name: sync_pair_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sync_pair_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_pair_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3705 (class 0 OID 0)
-- Dependencies: 243
-- Name: sync_pair_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sync_pair_id_seq OWNED BY public.sync_pair.id;


--
-- TOC entry 222 (class 1259 OID 65615)
-- Name: sync_pairs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sync_pairs (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    source_type character varying(50) NOT NULL,
    source_config text NOT NULL,
    target_type character varying(50) NOT NULL,
    target_config text NOT NULL,
    sync_frequency character varying(50),
    sync_schedule character varying(100),
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by_id integer NOT NULL
);


ALTER TABLE public.sync_pairs OWNER TO neondb_owner;

--
-- TOC entry 221 (class 1259 OID 65614)
-- Name: sync_pairs_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sync_pairs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_pairs_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3706 (class 0 OID 0)
-- Dependencies: 221
-- Name: sync_pairs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sync_pairs_id_seq OWNED BY public.sync_pairs.id;


--
-- TOC entry 231 (class 1259 OID 81930)
-- Name: sync_source_systems; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sync_source_systems (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    system_type character varying(50) NOT NULL,
    county_id character varying(20) NOT NULL,
    connection_type character varying(30) NOT NULL,
    connection_config text NOT NULL,
    auth_type character varying(30),
    auth_config text,
    schema_mapping json,
    is_active boolean,
    last_successful_sync timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by character varying(100)
);


ALTER TABLE public.sync_source_systems OWNER TO neondb_owner;

--
-- TOC entry 230 (class 1259 OID 81929)
-- Name: sync_source_systems_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sync_source_systems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_source_systems_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3707 (class 0 OID 0)
-- Dependencies: 230
-- Name: sync_source_systems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sync_source_systems_id_seq OWNED BY public.sync_source_systems.id;


--
-- TOC entry 248 (class 1259 OID 122901)
-- Name: system_metric; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.system_metric (
    id integer NOT NULL,
    service character varying(50) NOT NULL,
    metric_name character varying(100) NOT NULL,
    metric_value double precision,
    "timestamp" timestamp without time zone,
    metric_metadata json
);


ALTER TABLE public.system_metric OWNER TO neondb_owner;

--
-- TOC entry 247 (class 1259 OID 122900)
-- Name: system_metric_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.system_metric_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_metric_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3708 (class 0 OID 0)
-- Dependencies: 247
-- Name: system_metric_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.system_metric_id_seq OWNED BY public.system_metric.id;


--
-- TOC entry 216 (class 1259 OID 65576)
-- Name: system_metrics; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.system_metrics (
    id integer NOT NULL,
    "timestamp" timestamp without time zone,
    cpu_usage double precision,
    memory_usage double precision,
    disk_usage double precision,
    api_requests integer,
    active_syncs integer,
    active_users integer,
    syncservice_health character varying(20),
    api_gateway_health character varying(20),
    database_health character varying(20),
    average_response_time double precision,
    error_rate double precision,
    raw_metrics text
);


ALTER TABLE public.system_metrics OWNER TO neondb_owner;

--
-- TOC entry 215 (class 1259 OID 65575)
-- Name: system_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.system_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_metrics_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3709 (class 0 OID 0)
-- Dependencies: 215
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- TOC entry 218 (class 1259 OID 65585)
-- Name: user_onboarding; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.user_onboarding (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(50) NOT NULL,
    current_step integer,
    progress text,
    tutorial_complete boolean,
    last_activity timestamp without time zone,
    completion_date timestamp without time zone,
    dismissed boolean
);


ALTER TABLE public.user_onboarding OWNER TO neondb_owner;

--
-- TOC entry 217 (class 1259 OID 65584)
-- Name: user_onboarding_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.user_onboarding_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_onboarding_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3710 (class 0 OID 0)
-- Dependencies: 217
-- Name: user_onboarding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.user_onboarding_id_seq OWNED BY public.user_onboarding.id;


--
-- TOC entry 254 (class 1259 OID 131103)
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(256),
    first_name character varying(64),
    last_name character varying(64),
    county character varying(64),
    role character varying(32),
    created_at timestamp without time zone,
    last_login timestamp without time zone,
    is_active boolean
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- TOC entry 253 (class 1259 OID 131102)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3711 (class 0 OID 0)
-- Dependencies: 253
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 3322 (class 2604 OID 65632)
-- Name: audit_entries id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.audit_entries ALTER COLUMN id SET DEFAULT nextval('public.audit_entries_id_seq'::regclass);


--
-- TOC entry 3332 (class 2604 OID 122913)
-- Name: audit_entry id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.audit_entry ALTER COLUMN id SET DEFAULT nextval('public.audit_entry_id_seq'::regclass);


--
-- TOC entry 3335 (class 2604 OID 131119)
-- Name: counties id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.counties ALTER COLUMN id SET DEFAULT nextval('public.counties_id_seq'::regclass);


--
-- TOC entry 3330 (class 2604 OID 122893)
-- Name: gis_export_job id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.gis_export_job ALTER COLUMN id SET DEFAULT nextval('public.gis_export_job_id_seq'::regclass);


--
-- TOC entry 3336 (class 2604 OID 131128)
-- Name: gis_export_jobs id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.gis_export_jobs ALTER COLUMN id SET DEFAULT nextval('public.gis_export_jobs_id_seq'::regclass);


--
-- TOC entry 3328 (class 2604 OID 81970)
-- Name: import_jobs id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.import_jobs ALTER COLUMN id SET DEFAULT nextval('public.import_jobs_id_seq'::regclass);


--
-- TOC entry 3324 (class 2604 OID 73732)
-- Name: onboarding_event id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.onboarding_event ALTER COLUMN id SET DEFAULT nextval('public.onboarding_event_id_seq'::regclass);


--
-- TOC entry 3320 (class 2604 OID 65604)
-- Name: onboarding_events id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.onboarding_events ALTER COLUMN id SET DEFAULT nextval('public.onboarding_events_id_seq'::regclass);


--
-- TOC entry 3327 (class 2604 OID 81956)
-- Name: property_improvements id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.property_improvements ALTER COLUMN id SET DEFAULT nextval('public.property_improvements_id_seq'::regclass);


--
-- TOC entry 3326 (class 2604 OID 81942)
-- Name: property_valuations id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.property_valuations ALTER COLUMN id SET DEFAULT nextval('public.property_valuations_id_seq'::regclass);


--
-- TOC entry 3343 (class 2604 OID 139285)
-- Name: rbac_audit_log id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.rbac_audit_log ALTER COLUMN id SET DEFAULT nextval('public.rbac_audit_log_id_seq'::regclass);


--
-- TOC entry 3345 (class 2604 OID 139295)
-- Name: rbac_sessions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.rbac_sessions ALTER COLUMN id SET DEFAULT nextval('public.rbac_sessions_id_seq'::regclass);


--
-- TOC entry 3338 (class 2604 OID 139268)
-- Name: rbac_users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.rbac_users ALTER COLUMN id SET DEFAULT nextval('public.rbac_users_id_seq'::regclass);


--
-- TOC entry 3337 (class 2604 OID 131149)
-- Name: sync_jobs id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sync_jobs ALTER COLUMN id SET DEFAULT nextval('public.sync_jobs_id_seq'::regclass);


--
-- TOC entry 3333 (class 2604 OID 122922)
-- Name: sync_operation id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sync_operation ALTER COLUMN id SET DEFAULT nextval('public.sync_operation_id_seq'::regclass);


--
-- TOC entry 3323 (class 2604 OID 65646)
-- Name: sync_operations id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sync_operations ALTER COLUMN id SET DEFAULT nextval('public.sync_operations_id_seq'::regclass);


--
-- TOC entry 3329 (class 2604 OID 122884)
-- Name: sync_pair id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sync_pair ALTER COLUMN id SET DEFAULT nextval('public.sync_pair_id_seq'::regclass);


--
-- TOC entry 3321 (class 2604 OID 65618)
-- Name: sync_pairs id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sync_pairs ALTER COLUMN id SET DEFAULT nextval('public.sync_pairs_id_seq'::regclass);


--
-- TOC entry 3325 (class 2604 OID 81933)
-- Name: sync_source_systems id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sync_source_systems ALTER COLUMN id SET DEFAULT nextval('public.sync_source_systems_id_seq'::regclass);


--
-- TOC entry 3331 (class 2604 OID 122904)
-- Name: system_metric id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_metric ALTER COLUMN id SET DEFAULT nextval('public.system_metric_id_seq'::regclass);


--
-- TOC entry 3318 (class 2604 OID 65579)
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- TOC entry 3319 (class 2604 OID 65588)
-- Name: user_onboarding id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_onboarding ALTER COLUMN id SET DEFAULT nextval('public.user_onboarding_id_seq'::regclass);


--
-- TOC entry 3334 (class 2604 OID 131106)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3624 (class 0 OID 98315)
-- Dependencies: 242
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.alembic_version (version_num) FROM stdin;
a45c7931dd6e
\.


--
-- TOC entry 3606 (class 0 OID 65629)
-- Dependencies: 224
-- Data for Name: audit_entries; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.audit_entries (id, "timestamp", event_type, severity, resource_type, resource_id, operation_id, description, previous_state, new_state, user_id, username, ip_address, additional_data, correlation_id) FROM stdin;
1	2025-05-08 18:37:33.435986	login_failed	warning	auth	\N	\N	Failed login attempt for user admin	\N	\N	\N	admin	10.82.9.65	\N	\N
44	2025-05-09 19:43:12.456244	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
35	2025-05-09 19:37:23.570898	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
36	2025-05-09 19:38:06.525613	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
37	2025-05-09 19:38:06.594274	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
38	2025-05-09 19:38:10.506813	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
39	2025-05-09 19:38:48.899706	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
40	2025-05-09 19:39:07.603287	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
41	2025-05-09 19:40:37.334984	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
42	2025-05-09 19:41:37.257808	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
43	2025-05-09 19:42:37.600482	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
45	2025-05-09 19:43:12.529456	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
46	2025-05-09 19:43:16.356542	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
47	2025-05-09 19:43:54.844293	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
48	2025-05-09 19:44:16.631874	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
49	2025-05-09 19:45:13.110063	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
50	2025-05-09 19:46:43.230705	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
51	2025-05-09 19:46:52.409889	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
52	2025-05-09 19:46:52.494666	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
53	2025-05-09 19:46:56.272502	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
54	2025-05-09 19:47:34.859031	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
55	2025-05-09 19:47:57.055499	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
56	2025-05-09 19:49:25.735932	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
57	2025-05-09 19:49:25.792512	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
58	2025-05-09 19:50:53.480053	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
59	2025-05-09 19:51:53.788069	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
60	2025-05-09 19:52:53.477831	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
61	2025-05-09 19:53:43.797544	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
62	2025-05-09 19:53:43.88628	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
63	2025-05-09 19:53:47.673721	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
64	2025-05-09 19:54:12.348984	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
65	2025-05-09 19:54:44.691093	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
66	2025-05-09 19:56:14.714209	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
67	2025-05-09 19:57:44.515161	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
68	2025-05-09 19:58:44.831194	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
69	2025-05-09 19:58:50.917599	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
70	2025-05-09 19:58:50.988445	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
71	2025-05-09 19:58:54.797521	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
72	2025-05-09 19:59:11.31986	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
73	2025-05-09 19:59:51.497183	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
74	2025-05-09 20:00:27.128584	service_health_check_error	error	system	unknown	\N	Error during SyncService health check: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))	\N	\N	\N	system	\N	\N	\N
75	2025-05-09 20:00:27.222743	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
76	2025-05-09 20:01:27.959785	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
77	2025-05-09 20:02:57.635916	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
78	2025-05-09 20:03:57.763256	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
79	2025-05-09 20:05:27.873566	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
80	2025-05-09 20:06:27.948232	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
81	2025-05-09 20:07:27.641847	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
82	2025-05-09 20:08:27.620342	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
83	2025-05-09 20:09:27.642514	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
84	2025-05-09 20:10:57.969207	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
85	2025-05-09 20:12:27.968815	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
86	2025-05-09 20:13:27.766612	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
87	2025-05-09 20:14:27.664747	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
88	2025-05-09 20:15:27.955396	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
89	2025-05-09 20:16:58.149639	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
90	2025-05-09 20:17:57.77419	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
91	2025-05-09 20:19:27.623489	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
92	2025-05-09 20:20:27.662569	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
93	2025-05-09 20:21:57.739282	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
94	2025-05-09 20:22:31.965755	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
95	2025-05-09 20:22:32.029446	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
96	2025-05-09 20:22:35.853962	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
97	2025-05-09 20:23:00.398189	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
98	2025-05-09 20:23:32.634905	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
99	2025-05-09 20:23:49.034208	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
100	2025-05-09 20:23:49.100598	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
101	2025-05-09 20:23:53.020628	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
102	2025-05-09 20:24:09.531632	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
103	2025-05-09 20:24:50.160842	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
104	2025-05-09 20:25:50.043894	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
105	2025-05-09 20:26:25.494572	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
106	2025-05-09 20:26:25.567349	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
107	2025-05-09 20:26:29.360471	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
108	2025-05-09 20:26:45.952805	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
109	2025-05-09 20:27:26.14227	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
110	2025-05-09 20:28:10.644792	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
111	2025-05-09 20:28:10.713692	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
112	2025-05-09 20:28:14.529034	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
113	2025-05-09 20:28:31.146708	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
146	2025-05-09 20:49:28.965506	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
114	2025-05-09 20:29:11.740024	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
115	2025-05-09 20:30:17.095748	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
116	2025-05-09 20:30:17.166758	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
117	2025-05-09 20:30:20.975068	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
118	2025-05-09 20:30:33.532736	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
119	2025-05-09 20:31:18.008828	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
120	2025-05-09 20:32:17.905535	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
121	2025-05-09 20:32:41.039338	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
122	2025-05-09 20:32:41.10798	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
123	2025-05-09 20:32:44.915271	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
124	2025-05-09 20:33:01.499584	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
125	2025-05-09 20:33:41.845641	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
126	2025-05-09 20:35:11.734485	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
127	2025-05-09 20:35:49.725554	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
128	2025-05-09 20:36:54.610371	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
129	2025-05-09 20:36:54.662823	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
130	2025-05-09 20:37:50.750065	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
131	2025-05-09 20:38:50.943117	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
132	2025-05-09 20:40:20.605654	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
133	2025-05-09 20:41:20.550583	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
134	2025-05-09 20:42:20.599066	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
135	2025-05-09 20:43:50.964042	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
136	2025-05-09 20:45:20.716814	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
137	2025-05-09 20:46:13.208958	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
138	2025-05-09 20:46:13.287951	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
139	2025-05-09 20:46:17.060259	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
140	2025-05-09 20:46:33.839119	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
141	2025-05-09 20:47:15.024769	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
142	2025-05-09 20:48:24.508398	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
143	2025-05-09 20:48:24.581349	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
144	2025-05-09 20:48:28.473417	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
145	2025-05-09 20:49:07.171909	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
147	2025-05-09 20:49:39.057783	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
148	2025-05-09 20:49:39.130755	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
149	2025-05-09 20:49:42.901615	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
150	2025-05-09 20:49:59.663307	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
151	2025-05-09 20:50:39.902671	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
152	2025-05-09 20:51:34.625895	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
153	2025-05-09 20:51:34.698884	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
154	2025-05-09 20:51:38.497608	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
155	2025-05-09 20:51:55.392215	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
156	2025-05-09 20:52:35.729308	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
157	2025-05-09 20:53:08.767831	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
158	2025-05-09 20:53:08.856758	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
159	2025-05-09 20:53:12.679397	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
160	2025-05-09 20:53:51.633245	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
161	2025-05-09 20:54:10.027296	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
162	2025-05-09 20:55:06.158396	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
163	2025-05-09 20:55:06.272558	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
164	2025-05-09 20:55:09.983197	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
165	2025-05-09 20:55:35.292274	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
166	2025-05-09 20:56:06.893419	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
167	2025-05-09 20:56:29.100699	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
168	2025-05-09 20:56:29.192871	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
169	2025-05-09 20:56:32.90455	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
170	2025-05-09 20:56:43.690302	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
171	2025-05-09 20:57:30.911186	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
172	2025-05-09 20:58:34.43769	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
173	2025-05-09 20:58:34.542839	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
174	2025-05-09 20:58:38.390278	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
175	2025-05-09 20:58:55.064484	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
176	2025-05-09 20:59:35.590032	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
177	2025-05-09 21:00:35.566849	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
178	2025-05-09 21:01:35.623298	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
179	2025-05-09 21:02:00.626035	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
180	2025-05-09 21:02:00.695175	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
181	2025-05-09 21:02:04.505588	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
182	2025-05-09 21:02:29.201537	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
183	2025-05-09 21:03:01.86038	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
184	2025-05-09 21:04:41.087415	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
185	2025-05-09 21:04:41.25353	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
186	2025-05-09 21:04:44.989114	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
187	2025-05-09 21:05:24.137585	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 3 attempt(s)	\N	\N	\N	system	\N	\N	\N
188	2025-05-09 21:05:42.838265	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
189	2025-05-09 21:06:42.407813	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
190	2025-05-09 21:07:28.742832	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
191	2025-05-09 21:07:28.818965	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
192	2025-05-09 21:07:32.678459	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
193	2025-05-09 21:07:57.602893	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
194	2025-05-09 21:08:30.133845	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
195	2025-05-09 21:09:52.419597	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
196	2025-05-09 21:09:52.491117	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
197	2025-05-09 21:09:56.273072	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
198	2025-05-09 21:10:34.985226	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
199	2025-05-09 21:10:54.118818	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
200	2025-05-09 21:10:57.64411	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
201	2025-05-09 21:11:59.067453	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
202	2025-05-09 21:12:08.322033	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
203	2025-05-09 21:12:08.412506	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
204	2025-05-09 21:12:12.164592	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
205	2025-05-09 21:12:36.913429	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
206	2025-05-09 21:13:09.875211	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
207	2025-05-09 21:13:51.506079	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
208	2025-05-09 21:13:51.597725	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
209	2025-05-09 21:13:55.438393	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
210	2025-05-09 21:14:12.150733	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
211	2025-05-09 21:14:52.872313	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
212	2025-05-09 21:15:36.3667	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
213	2025-05-09 21:15:36.430825	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
214	2025-05-09 21:15:40.270346	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
215	2025-05-09 21:15:56.933564	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
216	2025-05-09 21:16:37.923798	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
217	2025-05-09 21:18:07.777093	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
218	2025-05-09 21:19:37.853029	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
219	2025-05-09 21:20:44.099234	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
220	2025-05-09 21:20:44.173558	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
221	2025-05-09 21:20:47.889832	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
222	2025-05-09 21:21:04.807726	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
223	2025-05-09 21:21:49.927074	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
224	2025-05-09 21:21:49.990865	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
225	2025-05-09 21:22:18.392902	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
226	2025-05-09 21:22:18.467412	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
227	2025-05-09 21:22:22.361511	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
228	2025-05-09 21:23:01.059119	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
229	2025-05-09 21:23:19.921287	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
230	2025-05-09 21:24:16.529749	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
231	2025-05-09 21:24:16.640454	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
232	2025-05-09 21:24:20.480465	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
233	2025-05-09 21:24:37.186446	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
234	2025-05-09 21:25:18.069837	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
235	2025-05-09 21:26:36.025353	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
236	2025-05-09 21:26:36.101656	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
237	2025-05-09 21:26:39.981947	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
238	2025-05-09 21:26:56.765372	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
239	2025-05-09 21:27:37.307878	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
240	2025-05-09 21:28:37.953895	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
241	2025-05-09 21:29:12.559068	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
242	2025-05-09 21:29:12.654469	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
243	2025-05-09 21:29:16.331239	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
244	2025-05-09 21:29:41.498425	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
245	2025-05-09 21:30:14.108122	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
246	2025-05-09 21:31:13.904915	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
247	2025-05-09 21:32:53.156578	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
248	2025-05-09 21:33:53.344621	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
249	2025-05-09 21:34:53.222071	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
250	2025-05-09 21:36:53.463009	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
251	2025-05-09 21:38:53.337457	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
252	2025-05-09 21:39:53.581021	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
253	2025-05-09 21:40:53.092553	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
254	2025-05-09 21:41:53.481513	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
255	2025-05-09 21:42:53.315323	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
256	2025-05-09 21:44:53.256375	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
257	2025-05-09 21:45:53.245623	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
258	2025-05-09 22:01:43.557705	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
259	2025-05-09 22:02:43.618145	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
260	2025-05-09 22:03:44.041002	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
261	2025-05-09 22:04:53.119454	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
262	2025-05-09 22:05:40.781719	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
263	2025-05-09 22:05:40.850938	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
264	2025-05-09 22:05:44.770982	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
265	2025-05-09 22:06:09.213488	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
266	2025-05-09 22:06:42.897	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
267	2025-05-09 22:07:43.086853	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
268	2025-05-09 22:08:43.345634	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
269	2025-05-09 22:08:43.431763	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
270	2025-05-09 22:08:47.170712	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
271	2025-05-09 22:09:11.845114	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
272	2025-05-09 22:09:45.062662	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
273	2025-05-09 22:10:44.911363	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
274	2025-05-09 22:11:53.105413	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
275	2025-05-09 22:12:53.151281	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
276	2025-05-09 22:13:53.28879	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
277	2025-05-09 22:15:53.247404	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
278	2025-05-09 22:19:13.678517	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
279	2025-05-09 22:19:13.767228	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
280	2025-05-09 22:19:17.659192	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
281	2025-05-09 22:19:56.096302	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
282	2025-05-09 22:20:47.610347	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
283	2025-05-09 22:21:44.148429	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
284	2025-05-09 22:21:49.572661	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
285	2025-05-09 22:22:50.515679	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
286	2025-05-09 22:23:50.594965	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
287	2025-05-09 22:24:50.381845	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
288	2025-05-09 22:26:20.555529	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
289	2025-05-09 22:27:24.081152	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
290	2025-05-09 22:30:04.555187	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
291	2025-05-09 22:30:04.618016	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
292	2025-05-09 22:30:53.428014	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
293	2025-05-09 22:31:53.61448	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
294	2025-05-09 22:33:23.43258	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
295	2025-05-09 22:34:24.356942	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
296	2025-05-09 22:34:40.005239	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
297	2025-05-09 22:35:53.309775	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
298	2025-05-09 22:36:53.459638	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
299	2025-05-09 22:37:54.334002	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
300	2025-05-09 22:39:15.602431	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
301	2025-05-09 22:40:15.337737	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
302	2025-05-09 22:41:45.796561	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
303	2025-05-09 22:42:45.568568	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
304	2025-05-09 22:43:45.162776	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
305	2025-05-09 22:44:45.445559	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
306	2025-05-09 22:45:45.633118	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
307	2025-05-09 22:47:17.19621	login_failed	warning	auth	unknown	\N	Failed login attempt for user admin	\N	\N	\N	admin	10.82.8.83	\N	\N
308	2025-05-09 22:47:17.69278	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
309	2025-05-09 22:49:28.657993	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
310	2025-05-09 22:49:35.20527	login_failed	warning	auth	unknown	\N	Failed login attempt for user admin	\N	\N	\N	admin	10.82.5.175	\N	\N
311	2025-05-09 22:51:53.073279	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
312	2025-05-09 22:57:03.427915	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.6.69	\N	\N
313	2025-05-09 22:57:04.707555	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
314	2025-05-09 22:57:11.579853	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.6.69	\N	\N
315	2025-05-09 22:57:25.6195	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.2.153	\N	\N
316	2025-05-09 22:59:34.371684	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
317	2025-05-09 22:59:35.79771	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
318	2025-05-09 22:59:38.036869	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
319	2025-05-09 23:00:20.321996	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
320	2025-05-09 23:07:21.751411	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
321	2025-05-09 23:09:07.698513	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
322	2025-05-09 23:10:05.221659	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.3.196	\N	\N
323	2025-05-09 23:12:54.557324	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
324	2025-05-09 23:15:43.685981	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
325	2025-05-09 23:16:53.401633	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
326	2025-05-09 23:17:57.928634	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
327	2025-05-09 23:19:37.697772	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
328	2025-05-09 23:20:07.093705	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
329	2025-05-09 23:20:07.434654	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
330	2025-05-09 23:20:07.734522	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
331	2025-05-09 23:20:07.753425	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
332	2025-05-09 23:20:08.049135	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
333	2025-05-09 23:20:45.85892	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
334	2025-05-09 23:20:46.152737	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
335	2025-05-09 23:20:46.46516	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
336	2025-05-09 23:20:46.575969	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
337	2025-05-09 23:20:46.77434	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	127.0.0.1	\N	\N
338	2025-05-09 23:20:46.866642	login_success	info	auth	unknown	\N	User assessor logged in successfully as Assessor	\N	\N	\N	assessor	127.0.0.1	\N	\N
339	2025-05-09 23:20:46.977424	login_success	info	auth	unknown	\N	User staff logged in successfully as Staff	\N	\N	\N	staff	127.0.0.1	\N	\N
340	2025-05-09 23:20:47.087421	login_success	info	auth	unknown	\N	User auditor logged in successfully as Auditor	\N	\N	\N	auditor	127.0.0.1	\N	\N
341	2025-05-09 23:20:58.527256	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
342	2025-05-09 23:22:43.137208	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.4.160	\N	\N
343	2025-05-09 23:22:44.837867	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
344	2025-05-09 23:22:44.894414	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
345	2025-05-09 23:23:38.95525	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
346	2025-05-09 23:26:30.012584	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
347	2025-05-09 23:26:38.276274	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.0.176	\N	\N
348	2025-05-09 23:30:57.655846	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
349	2025-05-09 23:34:42.810524	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
350	2025-05-09 23:34:45.339368	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
351	2025-05-09 23:34:45.386496	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
352	2025-05-09 23:36:45.917506	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
353	2025-05-09 23:39:35.985224	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
354	2025-05-09 23:41:28.456059	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
355	2025-05-09 23:43:22.336184	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
356	2025-05-09 23:44:46.664209	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
357	2025-05-09 23:47:12.21171	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
358	2025-05-12 17:34:07.942434	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
359	2025-05-12 17:36:02.402076	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
360	2025-05-12 17:37:24.85256	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
361	2025-05-12 17:38:50.638506	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
362	2025-05-12 17:41:05.119437	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.12.32	\N	\N
363	2025-05-12 17:41:05.397843	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.6.59	\N	\N
364	2025-05-12 17:41:11.775953	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
365	2025-05-12 17:41:11.833798	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
366	2025-05-12 17:41:18.945565	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.11.43	\N	\N
367	2025-05-12 17:47:11.042262	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
368	2025-05-12 17:48:57.98622	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
369	2025-05-12 17:48:59.210659	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
370	2025-05-12 17:51:33.898596	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
371	2025-05-12 17:59:37.298201	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
372	2025-05-12 18:03:05.709542	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
373	2025-05-12 18:03:07.166793	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
374	2025-05-12 18:06:20.054457	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
375	2025-05-12 18:07:22.530337	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
376	2025-05-12 18:08:22.115059	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
377	2025-05-12 18:09:59.24085	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
378	2025-05-12 18:10:29.513837	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
379	2025-05-12 18:11:59.29155	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
380	2025-05-12 18:13:59.144589	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
381	2025-05-12 18:14:59.233091	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
382	2025-05-12 18:15:59.175369	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
383	2025-05-12 18:17:59.628799	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
384	2025-05-12 18:19:59.557495	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
385	2025-05-12 18:21:02.044822	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
386	2025-05-12 18:22:59.354349	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
387	2025-05-12 18:23:59.888409	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
388	2025-05-12 18:26:00.565627	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
389	2025-05-12 18:26:59.172223	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
390	2025-05-12 18:28:59.458532	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
391	2025-05-12 18:29:59.739077	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
392	2025-05-12 18:32:00.314207	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
393	2025-05-12 18:32:59.246505	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
394	2025-05-12 18:33:59.728079	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
395	2025-05-12 18:35:59.650713	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
396	2025-05-12 18:37:59.303239	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
397	2025-05-12 18:39:59.50419	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
544	2025-05-12 22:50:55.005785	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
398	2025-05-12 18:41:00.376635	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
399	2025-05-12 18:42:00.149437	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
400	2025-05-12 18:43:59.906236	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
401	2025-05-12 18:45:59.631716	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
402	2025-05-12 18:46:59.85074	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
403	2025-05-12 18:48:00.39906	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
404	2025-05-12 18:49:59.5077	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
405	2025-05-12 18:50:59.737223	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
406	2025-05-12 18:52:59.709264	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
407	2025-05-12 18:53:59.438222	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
408	2025-05-12 18:55:59.398936	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
409	2025-05-12 18:57:00.116586	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
410	2025-05-12 18:57:59.532787	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
411	2025-05-12 18:59:59.667531	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
412	2025-05-12 19:02:06.094099	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
413	2025-05-12 19:02:06.153703	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
414	2025-05-12 19:18:20.751737	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
415	2025-05-12 19:20:40.250034	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
416	2025-05-12 19:31:23.051791	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
417	2025-05-12 19:33:52.818037	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
418	2025-05-12 19:36:22.313547	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
419	2025-05-12 19:38:05.019994	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
420	2025-05-12 19:40:41.01369	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
637	2025-05-12 23:44:03.002449	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
643	2025-05-12 23:50:59.044812	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
421	2025-05-12 19:42:43.933756	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
422	2025-05-12 19:44:48.005713	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
423	2025-05-12 19:54:24.690213	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
424	2025-05-12 20:00:28.55948	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
425	2025-05-12 20:04:13.903894	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
426	2025-05-12 20:04:14.855698	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
427	2025-05-12 20:05:37.351494	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
428	2025-05-12 20:06:46.64362	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
429	2025-05-12 20:06:46.690818	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
430	2025-05-12 20:08:09.566832	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
431	2025-05-12 20:09:40.261253	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
432	2025-05-12 20:10:40.391581	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
433	2025-05-12 20:11:39.383216	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
434	2025-05-12 20:11:59.214177	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
435	2025-05-12 20:12:34.844402	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
436	2025-05-12 20:13:59.92279	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
437	2025-05-12 20:14:36.457488	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
438	2025-05-12 20:16:02.079901	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
439	2025-05-12 20:16:33.610582	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
440	2025-05-12 20:17:00.818053	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
441	2025-05-12 20:17:10.217437	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
442	2025-05-12 20:18:40.631258	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
443	2025-05-12 20:19:33.735566	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
444	2025-05-12 20:19:57.795236	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
638	2025-05-12 23:44:59.159305	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
445	2025-05-12 20:20:33.778407	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
446	2025-05-12 20:21:39.528745	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
447	2025-05-12 20:22:59.344014	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
448	2025-05-12 20:23:59.832247	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
449	2025-05-12 20:24:59.752142	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
450	2025-05-12 20:25:59.602462	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
451	2025-05-12 20:27:09.561283	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
452	2025-05-12 20:27:37.349371	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
453	2025-05-12 20:28:41.099035	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
454	2025-05-12 20:29:59.533519	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
455	2025-05-12 20:30:59.646189	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
456	2025-05-12 20:32:14.809784	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
457	2025-05-12 20:32:14.8624	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
458	2025-05-12 20:32:47.61403	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
459	2025-05-12 20:34:00.08926	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
460	2025-05-12 20:35:00.06166	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
461	2025-05-12 20:35:59.877455	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
462	2025-05-12 20:37:59.562816	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
463	2025-05-12 20:39:00.037566	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
464	2025-05-12 20:39:59.750642	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
465	2025-05-12 20:41:00.696897	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
466	2025-05-12 20:42:59.786873	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
467	2025-05-12 20:43:59.686635	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
639	2025-05-12 23:45:03.061731	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
644	2025-05-12 23:51:03.059272	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
468	2025-05-12 20:45:00.667567	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
470	2025-05-12 20:47:59.44273	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
469	2025-05-12 20:45:59.790053	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
471	2025-05-12 20:49:00.262343	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
472	2025-05-12 20:49:59.408915	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
473	2025-05-12 20:51:00.335027	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
474	2025-05-12 20:52:59.420885	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
475	2025-05-12 20:53:59.544484	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
476	2025-05-12 20:54:59.978586	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
477	2025-05-12 20:56:00.11852	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
478	2025-05-12 20:57:09.751679	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
479	2025-05-12 20:58:39.657867	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
480	2025-05-12 20:59:39.402314	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
481	2025-05-12 20:59:52.7538	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
482	2025-05-12 21:01:00.180197	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
483	2025-05-12 21:02:25.67361	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
484	2025-05-12 21:02:26.19007	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
485	2025-05-12 21:03:46.402532	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
486	2025-05-12 21:04:46.213866	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
487	2025-05-12 21:05:46.189014	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
488	2025-05-12 21:07:00.512771	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
489	2025-05-12 21:07:59.647806	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
490	2025-05-12 21:08:06.929342	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
491	2025-05-12 21:09:16.427112	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
492	2025-05-12 21:09:41.37468	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
640	2025-05-12 23:47:03.002933	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
641	2025-05-12 23:48:03.013407	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
493	2025-05-12 21:10:45.873573	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
494	2025-05-12 21:11:20.31016	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
495	2025-05-12 21:12:25.835597	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
496	2025-05-12 21:13:02.065003	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
497	2025-05-12 21:14:21.845557	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
498	2025-05-12 21:15:59.937749	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
499	2025-05-12 21:17:00.905463	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
500	2025-05-12 21:18:00.65497	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
501	2025-05-12 21:19:59.675827	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
502	2025-05-12 21:21:00.270436	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
503	2025-05-12 21:21:59.902335	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
504	2025-05-12 21:23:00.303406	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
505	2025-05-12 21:24:59.824902	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
506	2025-05-12 21:26:01.890332	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
507	2025-05-12 21:26:59.79598	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
508	2025-05-12 21:27:59.938802	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
509	2025-05-12 21:29:59.960281	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
510	2025-05-12 21:30:59.964868	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
511	2025-05-12 21:32:00.055106	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
512	2025-05-12 21:33:00.008041	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
513	2025-05-12 21:34:59.687657	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
514	2025-05-12 21:35:59.684832	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
515	2025-05-12 21:37:20.769785	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
642	2025-05-12 23:50:03.136437	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
516	2025-05-12 21:38:52.431254	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
517	2025-05-12 21:41:08.919142	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
518	2025-05-12 21:42:22.262726	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
519	2025-05-12 21:43:41.972308	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
520	2025-05-12 21:44:51.529706	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
521	2025-05-12 21:46:01.248316	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
522	2025-05-12 21:46:14.882281	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
523	2025-05-12 21:47:21.949105	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
524	2025-05-12 21:48:59.436709	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
525	2025-05-12 21:49:52.977206	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.13.48	\N	\N
526	2025-05-12 21:50:00.994197	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
527	2025-05-12 21:50:40.73911	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
528	2025-05-12 21:52:26.692035	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
529	2025-05-12 21:57:48.38798	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
530	2025-05-12 21:59:33.071189	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
531	2025-05-12 21:59:33.85594	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
532	2025-05-12 22:01:14.583254	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
533	2025-05-12 22:46:40.998279	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
534	2025-05-12 22:47:42.825708	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
535	2025-05-12 22:47:52.419333	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
536	2025-05-12 22:47:52.522641	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
537	2025-05-12 22:47:56.272872	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
538	2025-05-12 22:48:12.938202	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
539	2025-05-12 22:48:53.652185	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
540	2025-05-12 22:49:53.416751	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
541	2025-05-12 22:50:34.51526	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
542	2025-05-12 22:50:34.591624	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
543	2025-05-12 22:50:38.387972	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
545	2025-05-12 22:51:35.566683	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
546	2025-05-12 22:53:09.117377	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
547	2025-05-12 22:53:09.197264	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
548	2025-05-12 22:53:13.003721	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
549	2025-05-12 22:53:25.676347	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
550	2025-05-12 22:54:10.671763	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
551	2025-05-12 22:54:57.431213	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
552	2025-05-12 22:54:57.500438	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
553	2025-05-12 22:55:01.329143	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
554	2025-05-12 22:55:17.884045	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 2 attempt(s)	\N	\N	\N	system	\N	\N	\N
555	2025-05-12 22:55:58.360355	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
556	2025-05-12 22:56:39.885601	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
557	2025-05-12 22:56:39.986889	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
558	2025-05-12 22:56:43.866741	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
559	2025-05-12 22:57:14.485745	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 3 attempt(s)	\N	\N	\N	system	\N	\N	\N
560	2025-05-12 22:57:41.397554	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
561	2025-05-12 22:59:45.76086	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
562	2025-05-12 22:59:45.860764	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
563	2025-05-12 22:59:49.746582	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
564	2025-05-12 23:00:28.230355	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
565	2025-05-12 23:00:50.905903	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
566	2025-05-12 23:01:27.858982	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
567	2025-05-12 23:01:27.942691	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
568	2025-05-12 23:01:31.68327	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
569	2025-05-12 23:02:10.25672	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
570	2025-05-12 23:02:32.90294	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
571	2025-05-12 23:03:32.960146	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
572	2025-05-12 23:05:02.928848	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
573	2025-05-12 23:06:59.062872	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
574	2025-05-12 23:06:59.137387	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
575	2025-05-12 23:07:02.933239	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
576	2025-05-12 23:07:41.484298	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
577	2025-05-12 23:08:32.085035	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
578	2025-05-12 23:09:32.19464	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
579	2025-05-12 23:11:02.091786	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
580	2025-05-12 23:12:28.178462	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
581	2025-05-12 23:12:28.248556	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
582	2025-05-12 23:12:32.069445	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
583	2025-05-12 23:13:10.558879	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
584	2025-05-12 23:13:32.073897	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
585	2025-05-12 23:14:32.078023	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
586	2025-05-12 23:15:13.040775	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
587	2025-05-12 23:15:16.085057	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
588	2025-05-12 23:15:16.671488	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 2 attempts	\N	\N	\N	system	\N	\N	\N
589	2025-05-12 23:16:14.084406	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
590	2025-05-12 23:16:51.216813	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
591	2025-05-12 23:16:51.283905	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
592	2025-05-12 23:16:55.095974	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
593	2025-05-12 23:17:33.585877	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
594	2025-05-12 23:17:55.757997	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
595	2025-05-12 23:19:25.767133	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
596	2025-05-12 23:20:07.181638	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
597	2025-05-12 23:20:07.273638	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
598	2025-05-12 23:20:11.040416	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
599	2025-05-12 23:20:49.687778	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
600	2025-05-12 23:21:11.357004	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
601	2025-05-12 23:22:41.366649	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
602	2025-05-12 23:24:11.354509	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
603	2025-05-12 23:25:07.504104	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
604	2025-05-12 23:25:07.588316	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
605	2025-05-12 23:25:11.373151	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
606	2025-05-12 23:25:19.60623	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
607	2025-05-12 23:25:19.693363	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
608	2025-05-12 23:25:23.502119	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
609	2025-05-12 23:26:02.043591	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
610	2025-05-12 23:26:23.811477	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
611	2025-05-12 23:27:23.815938	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
612	2025-05-12 23:28:53.805624	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
613	2025-05-12 23:30:56.200289	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
614	2025-05-12 23:30:56.310202	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
615	2025-05-12 23:31:00.190454	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
616	2025-05-12 23:31:38.660791	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
617	2025-05-12 23:32:00.949807	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
618	2025-05-12 23:33:00.963464	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
619	2025-05-12 23:34:02.970252	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
620	2025-05-12 23:34:29.105573	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
621	2025-05-12 23:34:29.174131	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
622	2025-05-12 23:34:33.091316	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
623	2025-05-12 23:35:11.501104	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
624	2025-05-12 23:35:33.958113	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
625	2025-05-12 23:36:33.962148	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
626	2025-05-12 23:37:15.536106	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
627	2025-05-12 23:37:15.608975	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
628	2025-05-12 23:37:19.439049	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
629	2025-05-12 23:37:57.919782	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
630	2025-05-12 23:38:19.96669	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
631	2025-05-12 23:39:24.19326	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
632	2025-05-12 23:39:24.269594	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
633	2025-05-12 23:39:28.194201	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
634	2025-05-12 23:39:30.427014	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
635	2025-05-12 23:40:28.989332	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
636	2025-05-12 23:42:03.026469	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
645	2025-05-12 23:53:03.020093	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
646	2025-05-12 23:54:03.018983	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
647	2025-05-12 23:55:03.0088	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
648	2025-05-12 23:56:03.176477	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
649	2025-05-12 23:56:59.046333	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
650	2025-05-12 23:57:03.066021	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
651	2025-05-12 23:59:03.016444	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
652	2025-05-13 00:00:03.110942	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
653	2025-05-13 00:02:03.083197	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
654	2025-05-13 00:02:59.134187	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
655	2025-05-13 00:03:03.10324	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
656	2025-05-13 00:05:03.117464	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
657	2025-05-13 00:07:03.10913	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
658	2025-05-13 00:08:59.092726	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
659	2025-05-13 00:09:03.107256	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
660	2025-05-13 00:11:03.023248	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
661	2025-05-13 00:12:03.166462	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
662	2025-05-13 00:13:03.045324	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
663	2025-05-13 00:14:03.10432	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
664	2025-05-13 00:14:59.073383	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
665	2025-05-13 00:15:03.092493	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
666	2025-05-13 00:17:03.052226	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
667	2025-05-13 00:18:03.187509	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
668	2025-05-13 00:19:03.065665	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
669	2025-05-13 00:20:03.08131	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
670	2025-05-13 00:20:59.089806	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
671	2025-05-13 00:21:03.112223	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
672	2025-05-13 00:23:03.176054	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
673	2025-05-13 00:25:03.100762	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
674	2025-05-13 00:26:59.109219	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
675	2025-05-13 00:27:03.12424	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
676	2025-05-13 00:29:03.291416	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
677	2025-05-13 00:30:03.110512	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
678	2025-05-13 00:32:03.067302	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
679	2025-05-13 00:32:59.12112	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
680	2025-05-13 00:33:03.126384	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
681	2025-05-13 00:35:03.075984	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
682	2025-05-13 00:36:03.121012	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
683	2025-05-13 00:38:03.0745	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
684	2025-05-13 00:38:59.124943	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
685	2025-05-13 00:39:03.142484	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
686	2025-05-13 16:39:37.104788	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
687	2025-05-13 16:39:39.974684	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
688	2025-05-13 16:41:00.205226	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
689	2025-05-13 16:42:30.562906	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
690	2025-05-13 16:44:04.557413	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
691	2025-05-13 16:45:00.853761	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
692	2025-05-13 16:45:04.654083	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
693	2025-05-13 16:47:04.653086	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
694	2025-05-13 16:48:04.579707	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
695	2025-05-13 16:50:05.190568	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
696	2025-05-13 16:50:10.158235	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
697	2025-05-13 16:50:10.228259	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
698	2025-05-13 16:50:14.174942	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
699	2025-05-13 16:50:16.379363	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
700	2025-05-13 16:51:38.577354	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
701	2025-05-13 16:54:06.845138	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
702	2025-05-13 16:55:06.588199	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.1.30	\N	\N
703	2025-05-13 16:55:10.597828	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
704	2025-05-13 16:55:11.934315	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
705	2025-05-13 16:56:17.590778	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
706	2025-05-13 16:57:13.591668	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
707	2025-05-13 16:57:13.67644	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
708	2025-05-13 16:57:17.574221	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
709	2025-05-13 16:57:27.842939	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
710	2025-05-13 16:59:12.276105	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
711	2025-05-13 17:01:04.741666	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
712	2025-05-13 17:01:53.993891	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
713	2025-05-13 17:01:57.72016	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
714	2025-05-13 17:03:04.666217	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
715	2025-05-13 17:05:04.601387	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
716	2025-05-13 17:06:04.605625	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
717	2025-05-13 17:06:45.834015	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
718	2025-05-13 17:06:49.579318	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
719	2025-05-13 17:08:04.629504	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
720	2025-05-13 17:09:05.37628	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
721	2025-05-13 17:09:59.748557	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
722	2025-05-13 17:10:03.600728	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
723	2025-05-13 17:11:04.666874	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
724	2025-05-13 17:11:32.935034	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
725	2025-05-13 17:11:36.862153	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
726	2025-05-13 17:13:04.692367	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
727	2025-05-13 17:15:04.608163	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
728	2025-05-13 17:15:45.256131	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
729	2025-05-13 17:15:49.143068	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
730	2025-05-13 17:17:04.645719	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
731	2025-05-13 17:19:04.703936	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
732	2025-05-13 17:21:00.731743	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
733	2025-05-13 17:21:04.632723	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
734	2025-05-13 17:23:04.623186	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
735	2025-05-13 17:24:04.624999	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
736	2025-05-13 17:25:04.687342	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
737	2025-05-13 17:27:00.762428	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
738	2025-05-13 17:27:04.628312	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
739	2025-05-13 17:28:04.673437	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
740	2025-05-13 17:30:04.750416	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
741	2025-05-13 17:31:04.706059	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
742	2025-05-13 17:32:00.761386	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
743	2025-05-13 17:33:04.64061	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
744	2025-05-13 17:34:04.636246	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
745	2025-05-13 17:35:04.653782	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
746	2025-05-13 17:36:04.640578	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
747	2025-05-13 17:37:00.906327	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
748	2025-05-13 17:37:04.803801	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
749	2025-05-13 17:39:04.658466	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
750	2025-05-13 17:41:04.648426	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
751	2025-05-13 17:42:04.77156	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
752	2025-05-13 17:43:00.694582	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
753	2025-05-13 17:43:04.717753	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
754	2025-05-13 17:45:04.682475	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
755	2025-05-13 17:46:04.669217	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
756	2025-05-13 17:47:04.683417	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
757	2025-05-13 17:49:00.735151	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
758	2025-05-13 17:49:04.739574	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
759	2025-05-13 17:51:04.69786	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
760	2025-05-13 17:52:04.715313	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
761	2025-05-13 17:54:04.774252	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
762	2025-05-13 17:55:00.724578	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
763	2025-05-13 17:55:04.739905	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
764	2025-05-13 19:58:37.574047	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
765	2025-05-13 19:58:40.529347	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
766	2025-05-13 19:59:41.345142	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
767	2025-05-13 20:00:25.357519	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
768	2025-05-13 20:00:25.465213	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
769	2025-05-13 20:00:29.416246	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
770	2025-05-13 20:00:31.632647	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
771	2025-05-13 20:01:29.799021	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
772	2025-05-13 20:02:59.748284	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
773	2025-05-13 20:03:06.458108	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
774	2025-05-13 20:03:06.541217	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
775	2025-05-13 20:03:10.380293	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
776	2025-05-13 20:03:12.719977	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
777	2025-05-13 20:04:07.253545	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
778	2025-05-13 20:04:11.136957	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
779	2025-05-13 20:04:52.127549	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
780	2025-05-13 20:04:52.218857	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
781	2025-05-13 20:04:56.004578	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
782	2025-05-13 20:04:58.380241	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
783	2025-05-13 20:05:56.542132	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
784	2025-05-13 20:06:56.937265	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
785	2025-05-13 20:07:32.259887	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
786	2025-05-13 20:07:32.329161	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
787	2025-05-13 20:07:36.250644	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
788	2025-05-13 20:07:38.47378	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
789	2025-05-13 20:08:32.99961	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
790	2025-05-13 20:08:36.879505	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
791	2025-05-13 20:08:40.940075	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
792	2025-05-13 20:08:44.854643	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
793	2025-05-13 20:09:52.89481	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
794	2025-05-13 20:12:05.069344	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
795	2025-05-13 20:13:04.976562	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
796	2025-05-13 20:14:00.883675	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
797	2025-05-13 20:15:05.035606	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
798	2025-05-13 20:16:04.958062	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
799	2025-05-13 20:18:05.026964	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
800	2025-05-13 20:19:00.902445	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
801	2025-05-13 20:19:04.917609	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
802	2025-05-13 20:21:04.947505	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
803	2025-05-13 20:22:04.937383	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
804	2025-05-13 20:24:05.269142	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
805	2025-05-13 20:25:00.899688	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
806	2025-05-13 20:25:04.918295	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
807	2025-05-13 20:25:32.422734	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.7.35	\N	\N
808	2025-05-13 20:26:07.204046	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
809	2025-05-13 20:27:07.249781	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
810	2025-05-13 20:31:36.796482	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
811	2025-05-13 20:31:40.450228	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
812	2025-05-13 20:31:55.519199	login_success	info	auth	unknown	\N	User admin logged in successfully as ITAdmin	\N	\N	\N	admin	10.82.7.35	\N	\N
813	2025-05-13 20:34:27.327321	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
814	2025-05-13 20:34:31.275029	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
815	2025-05-13 20:46:45.183246	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
816	2025-05-13 20:46:48.816715	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
817	2025-05-13 20:48:25.836564	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
818	2025-05-13 20:49:15.814562	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
819	2025-05-13 20:49:19.64651	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
820	2025-05-13 20:50:36.344397	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
821	2025-05-13 21:05:22.050795	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
822	2025-05-13 21:05:25.57087	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
823	2025-05-13 21:06:05.991662	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
824	2025-05-13 21:06:10.006714	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
825	2025-05-13 21:07:10.008005	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
826	2025-05-13 21:09:07.447653	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
827	2025-05-13 21:11:05.552461	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
828	2025-05-13 21:12:01.007313	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
829	2025-05-13 21:13:05.01444	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
830	2025-05-13 21:14:05.005701	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
831	2025-05-13 21:16:05.530877	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
832	2025-05-13 21:16:35.250299	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
833	2025-05-13 21:16:39.261845	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
834	2025-05-13 21:17:49.477721	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
835	2025-05-13 21:18:58.003589	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
836	2025-05-13 21:20:28.412228	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
837	2025-05-13 21:21:00.988639	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
838	2025-05-13 21:21:05.014967	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
839	2025-05-13 21:22:04.999212	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
840	2025-05-13 21:23:05.071156	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
841	2025-05-13 21:25:05.57524	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
842	2025-05-13 21:26:00.998762	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
843	2025-05-13 21:27:10.079424	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
844	2025-05-13 21:29:07.492328	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
845	2025-05-13 21:31:03.462137	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
846	2025-05-13 21:31:05.004031	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
847	2025-05-13 21:32:05.008328	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
848	2025-05-13 21:33:05.010864	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
849	2025-05-13 21:35:05.52703	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
850	2025-05-13 21:36:00.997438	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
851	2025-05-13 21:37:05.119478	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
852	2025-05-13 21:39:05.509999	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
853	2025-05-13 21:41:01.010327	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
854	2025-05-13 21:41:05.033205	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
855	2025-05-13 21:42:05.066649	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
856	2025-05-13 21:43:05.10153	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
857	2025-05-13 21:45:05.495051	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
858	2025-05-13 21:46:01.020808	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
859	2025-05-13 21:46:05.036097	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
860	2025-05-13 21:48:05.553271	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
861	2025-05-13 21:49:05.093612	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
862	2025-05-13 21:51:01.506369	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
863	2025-05-13 21:51:05.057789	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
864	2025-05-13 21:52:05.059734	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
865	2025-05-13 21:54:05.546106	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
866	2025-05-13 21:55:05.109993	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
867	2025-05-13 21:56:01.044197	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
868	2025-05-13 21:57:05.064695	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
869	2025-05-13 21:59:05.574367	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
870	2025-05-13 22:00:05.071796	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
871	2025-05-13 22:01:01.13651	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
872	2025-05-13 22:01:05.142181	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
873	2025-05-13 22:03:06.265525	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
874	2025-05-13 22:05:05.61051	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
875	2025-05-13 22:07:01.638847	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
876	2025-05-13 22:07:05.111316	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
877	2025-05-13 22:09:07.605473	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
878	2025-05-13 22:10:05.073852	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
879	2025-05-13 22:12:05.614391	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
880	2025-05-13 22:13:01.104412	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
881	2025-05-13 22:13:05.117212	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
882	2025-05-13 22:15:06.228615	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
883	2025-05-13 22:16:05.079384	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
884	2025-05-13 22:17:05.086238	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
885	2025-05-13 22:18:21.243995	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
886	2025-05-13 22:18:24.147055	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
887	2025-05-13 22:19:50.084564	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
888	2025-05-13 22:19:50.188105	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
889	2025-05-13 22:19:54.073981	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
890	2025-05-13 22:20:04.346648	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
891	2025-05-13 22:21:05.084052	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
892	2025-05-13 22:22:18.669246	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
893	2025-05-13 22:25:01.213035	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
894	2025-05-13 22:26:05.092343	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
895	2025-05-13 22:28:05.675091	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
896	2025-05-13 22:30:01.661283	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
897	2025-05-13 22:30:05.155823	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
898	2025-05-13 22:32:07.565105	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
899	2025-05-13 22:33:05.109222	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
900	2025-05-13 22:34:05.121779	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
901	2025-05-13 22:36:01.833797	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
902	2025-05-13 22:36:05.230502	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
903	2025-05-13 22:38:07.803289	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
904	2025-05-13 22:40:05.669842	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
905	2025-05-13 22:41:05.126847	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
906	2025-05-13 22:42:01.187568	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
907	2025-05-13 22:42:05.200063	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
908	2025-05-13 22:44:05.248675	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
909	2025-05-13 22:44:27.665865	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
910	2025-05-13 22:44:31.579441	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
911	2025-05-13 22:46:00.858942	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
912	2025-05-13 22:46:04.871465	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
913	2025-05-13 22:47:05.138738	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
914	2025-05-13 22:48:05.187279	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
915	2025-05-13 22:50:05.772506	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
916	2025-05-13 22:51:01.258764	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
917	2025-05-13 22:51:05.154866	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
918	2025-05-13 22:53:07.653476	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
919	2025-05-13 22:54:05.347236	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
920	2025-05-13 22:56:07.641525	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
921	2025-05-13 23:10:01.184609	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
922	2025-05-13 23:10:05.214217	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
923	2025-05-13 23:10:13.402916	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
924	2025-05-13 23:10:17.277048	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
925	2025-05-13 23:12:07.759663	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
926	2025-05-13 23:14:07.626429	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
927	2025-05-13 23:15:05.326005	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
928	2025-05-13 23:16:01.284433	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
929	2025-05-13 23:17:05.174168	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
930	2025-05-13 23:18:05.249613	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
931	2025-05-13 23:20:05.84805	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
932	2025-05-13 23:21:01.260788	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
933	2025-05-13 23:22:05.185931	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
934	2025-05-13 23:48:49.10519	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
935	2025-05-13 23:48:53.025562	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
936	2025-05-13 23:52:42.095877	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
937	2025-05-13 23:52:45.872331	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
938	2025-05-13 23:54:47.154004	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
939	2025-05-13 23:54:51.026909	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
940	2025-05-14 01:11:13.014858	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
941	2025-05-14 01:11:16.893673	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
942	2025-05-14 01:14:17.382015	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
943	2025-05-14 01:14:19.323264	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
944	2025-05-14 01:15:57.351362	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
945	2025-05-14 01:16:01.259647	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
946	2025-05-14 01:17:45.787072	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
947	2025-05-14 01:17:49.668999	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
948	2025-05-14 01:19:20.719875	service_unhealthy	warning	system	unknown	\N	SyncService is responding but unhealthy (status code: 404)	\N	\N	\N	system	\N	\N	\N
949	2025-05-14 01:19:22.612477	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
950	2025-05-14 01:21:24.100589	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
951	2025-05-14 01:23:09.135534	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
952	2025-05-14 01:35:06.537192	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
953	2025-05-14 01:36:20.202342	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
954	2025-05-14 01:37:58.203927	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
955	2025-05-14 01:39:34.598621	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
956	2025-05-14 18:26:47.483576	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
957	2025-05-14 18:26:47.595705	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
958	2025-05-14 18:26:51.337065	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
959	2025-05-14 18:27:29.95262	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
960	2025-05-14 18:27:52.660519	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
961	2025-05-14 18:28:52.658835	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
962	2025-05-14 18:29:54.367764	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
963	2025-05-14 18:30:28.205131	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
964	2025-05-14 18:30:28.279784	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
965	2025-05-14 18:30:32.352182	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
966	2025-05-14 18:30:32.40474	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
967	2025-05-14 18:30:34.438854	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
968	2025-05-14 18:31:28.720921	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
969	2025-05-14 18:32:29.695503	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
970	2025-05-14 18:32:52.590046	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
971	2025-05-14 18:32:52.697992	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
972	2025-05-14 18:32:56.725172	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
973	2025-05-14 18:32:56.789128	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
974	2025-05-14 18:32:58.863999	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
975	2025-05-14 18:33:53.365194	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
976	2025-05-14 18:34:53.688687	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
977	2025-05-14 18:35:38.002533	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
978	2025-05-14 18:35:38.122179	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
979	2025-05-14 18:35:41.990186	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
980	2025-05-14 18:35:42.06107	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
981	2025-05-14 18:35:44.318636	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
982	2025-05-14 18:36:38.727737	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
983	2025-05-14 18:36:55.697755	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
984	2025-05-14 18:36:55.790943	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
985	2025-05-14 18:36:59.693258	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
986	2025-05-14 18:36:59.745536	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
987	2025-05-14 18:37:01.954227	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
988	2025-05-14 18:37:56.687126	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
989	2025-05-14 18:38:37.767519	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
990	2025-05-14 18:38:37.846403	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
991	2025-05-14 18:38:42.089755	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
992	2025-05-14 18:38:42.153968	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
993	2025-05-14 18:38:44.012677	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
994	2025-05-14 18:39:38.741374	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
995	2025-05-14 18:39:59.980721	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
996	2025-05-14 18:40:00.079255	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
997	2025-05-14 18:40:04.936257	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
998	2025-05-14 18:40:05.270004	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
999	2025-05-14 18:40:06.33934	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1000	2025-05-14 18:41:00.707751	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1001	2025-05-14 18:42:30.684427	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1002	2025-05-14 18:43:30.686394	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1003	2025-05-14 18:44:30.794936	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1004	2025-05-14 18:46:30.699032	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1005	2025-05-14 18:48:30.695948	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1006	2025-05-14 18:49:30.689547	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1119	2025-05-14 20:38:34.768148	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1007	2025-05-14 18:50:30.995991	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1008	2025-05-14 18:52:30.720012	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1009	2025-05-14 18:53:30.731402	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1010	2025-05-14 18:54:30.921586	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1011	2025-05-14 18:55:30.752222	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1012	2025-05-14 18:56:30.769495	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1013	2025-05-14 18:58:00.358715	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1014	2025-05-14 18:58:18.981085	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1015	2025-05-14 18:58:19.053994	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1016	2025-05-14 18:58:22.972022	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1017	2025-05-14 18:58:23.026376	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1018	2025-05-14 18:58:25.203555	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1019	2025-05-14 18:59:19.201472	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1020	2025-05-14 19:00:14.756855	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1021	2025-05-14 19:01:15.294707	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1022	2025-05-14 19:02:24.780424	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1023	2025-05-14 19:02:24.847411	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1024	2025-05-14 19:02:29.160105	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1025	2025-05-14 19:02:29.702802	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1026	2025-05-14 19:02:31.065048	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1027	2025-05-14 19:03:35.102168	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1028	2025-05-14 19:04:06.344645	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1029	2025-05-14 19:04:06.44845	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1030	2025-05-14 19:04:10.295032	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1031	2025-05-14 19:04:10.353161	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1032	2025-05-14 19:04:12.615288	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1033	2025-05-14 19:05:06.548655	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1034	2025-05-14 19:05:38.502752	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1035	2025-05-14 19:05:38.579596	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1036	2025-05-14 19:05:42.646463	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1037	2025-05-14 19:05:42.711039	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1038	2025-05-14 19:05:44.768243	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1039	2025-05-14 19:06:39.738592	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1040	2025-05-14 19:07:52.342004	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1041	2025-05-14 19:07:52.559141	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1042	2025-05-14 19:07:54.841181	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1043	2025-05-14 19:07:56.542811	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1044	2025-05-14 19:07:56.647013	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1045	2025-05-14 19:08:52.904485	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1046	2025-05-14 19:10:22.920956	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1047	2025-05-14 19:11:52.907355	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1048	2025-05-14 19:12:53.145359	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1049	2025-05-14 19:14:22.934467	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1050	2025-05-14 19:15:52.948211	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1051	2025-05-14 19:16:53.779971	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1052	2025-05-14 19:18:30.93281	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1053	2025-05-14 19:20:30.783106	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1054	2025-05-14 19:22:30.747354	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1055	2025-05-14 19:24:30.996342	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1056	2025-05-14 19:25:52.952392	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1057	2025-05-14 19:26:53.802858	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1058	2025-05-14 19:28:22.956651	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1059	2025-05-14 19:29:53.152283	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1060	2025-05-14 19:31:23.920243	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1061	2025-05-14 19:32:30.776185	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1062	2025-05-14 19:33:30.864784	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1063	2025-05-14 19:34:53.960381	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1120	2025-05-14 20:39:34.826686	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1064	2025-05-14 19:36:32.461708	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1065	2025-05-14 19:37:53.822176	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1066	2025-05-14 19:39:08.595486	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1067	2025-05-14 19:40:22.98015	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1068	2025-05-14 19:41:53.951095	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1069	2025-05-14 19:43:32.857939	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1070	2025-05-14 19:44:23.003939	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1071	2025-05-14 19:45:23.011506	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1072	2025-05-14 19:46:52.967776	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1073	2025-05-14 19:47:52.956486	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1074	2025-05-14 19:48:53.802956	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1075	2025-05-14 19:50:30.80615	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1076	2025-05-14 19:51:37.931178	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1077	2025-05-14 19:53:07.400003	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1078	2025-05-14 19:54:07.409892	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1079	2025-05-14 19:55:07.824063	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1080	2025-05-14 19:56:31.577711	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1081	2025-05-14 19:57:37.403372	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1082	2025-05-14 19:59:07.406669	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1083	2025-05-14 20:00:07.831643	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1084	2025-05-14 20:01:30.977613	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1085	2025-05-14 20:02:37.419194	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1086	2025-05-14 20:03:37.808034	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1087	2025-05-14 20:05:34.077953	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1088	2025-05-14 20:06:30.823231	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1089	2025-05-14 20:07:30.921655	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1090	2025-05-14 20:09:30.842748	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1091	2025-05-14 20:11:30.855663	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1092	2025-05-14 20:13:30.918166	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1093	2025-05-14 20:14:37.465446	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1094	2025-05-14 20:15:38.041534	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1095	2025-05-14 20:17:32.845257	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1096	2025-05-14 20:18:58.744414	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1097	2025-05-14 20:20:07.44206	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1098	2025-05-14 20:20:34.082834	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1099	2025-05-14 20:21:37.605233	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1100	2025-05-14 20:23:07.652537	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1101	2025-05-14 20:24:05.690122	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1102	2025-05-14 20:25:43.713821	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1103	2025-05-14 20:26:40.807598	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1104	2025-05-14 20:27:12.222878	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1105	2025-05-14 20:28:40.757993	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1106	2025-05-14 20:30:02.904179	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1107	2025-05-14 20:31:02.761363	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1108	2025-05-14 20:32:02.772058	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1109	2025-05-14 20:32:32.891209	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1110	2025-05-14 20:32:34.962886	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1111	2025-05-14 20:33:21.434606	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1112	2025-05-14 20:33:34.794094	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1113	2025-05-14 20:35:34.747013	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1114	2025-05-14 20:36:34.751251	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1115	2025-05-14 20:37:30.752526	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1116	2025-05-14 20:37:30.826711	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1117	2025-05-14 20:37:35.052861	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1118	2025-05-14 20:38:13.584374	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1121	2025-05-14 20:41:34.826784	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1122	2025-05-14 20:42:30.768925	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1123	2025-05-14 20:42:30.857855	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1124	2025-05-14 20:43:13.326812	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1125	2025-05-14 20:43:34.774917	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1126	2025-05-14 20:45:34.825461	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1127	2025-05-14 20:47:34.769592	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1128	2025-05-14 20:48:30.887407	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1129	2025-05-14 20:48:31.052262	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1130	2025-05-14 20:48:34.774875	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1131	2025-05-14 20:49:13.393404	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1132	2025-05-14 20:49:34.784045	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1133	2025-05-14 20:51:34.838428	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1134	2025-05-14 20:53:30.905553	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1135	2025-05-14 20:53:31.119082	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1136	2025-05-14 20:53:34.782342	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1137	2025-05-14 20:54:13.476177	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1138	2025-05-14 20:54:34.784938	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1139	2025-05-14 20:56:34.8302	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1140	2025-05-14 20:57:34.850804	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1141	2025-05-14 20:58:30.903417	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1142	2025-05-14 20:58:30.977183	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1143	2025-05-14 20:59:13.321584	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1144	2025-05-14 20:59:34.785059	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1145	2025-05-14 21:00:34.800882	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1146	2025-05-14 21:02:34.818506	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1147	2025-05-14 21:03:30.862885	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1148	2025-05-14 21:03:30.946587	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1149	2025-05-14 21:03:34.976439	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1150	2025-05-14 21:04:13.344883	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1151	2025-05-14 21:05:34.811183	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1152	2025-05-14 21:06:34.820438	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1153	2025-05-14 21:08:34.950802	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1154	2025-05-14 21:09:30.853539	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1155	2025-05-14 21:09:30.936095	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1156	2025-05-14 21:09:34.85482	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1157	2025-05-14 21:10:13.348387	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1158	2025-05-14 21:11:34.80537	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1159	2025-05-14 21:12:34.815682	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1160	2025-05-14 21:13:34.958734	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1161	2025-05-14 21:15:30.919523	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1162	2025-05-14 21:15:31.060108	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1163	2025-05-14 21:15:34.87497	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1164	2025-05-14 21:16:13.495671	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1165	2025-05-14 21:17:34.83398	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1166	2025-05-14 21:18:34.966032	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1167	2025-05-14 21:20:34.922948	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1168	2025-05-14 21:21:30.858663	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1169	2025-05-14 21:21:30.9357	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1170	2025-05-14 21:21:34.866552	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1171	2025-05-14 21:22:13.234974	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1172	2025-05-14 21:23:34.969076	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1173	2025-05-14 23:22:52.556759	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1174	2025-05-14 23:22:52.677446	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1175	2025-05-14 23:22:56.430915	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1176	2025-05-14 23:23:06.848876	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1177	2025-05-14 23:23:52.626272	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1178	2025-05-14 23:25:22.545793	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1179	2025-05-14 23:26:22.543354	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1180	2025-05-14 23:27:19.358392	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1181	2025-05-14 23:28:22.571377	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1182	2025-05-14 23:29:22.635403	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1183	2025-05-14 23:30:52.570671	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1184	2025-05-14 23:31:39.466413	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1185	2025-05-14 23:32:52.573652	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1186	2025-05-14 23:34:15.855671	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1187	2025-05-14 23:35:45.85677	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1188	2025-05-14 23:36:45.975896	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1189	2025-05-14 23:37:46.231977	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1190	2025-05-14 23:39:15.860874	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1191	2025-05-14 23:40:15.871688	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1192	2025-05-14 23:41:15.887679	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1193	2025-05-14 23:42:15.879094	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1194	2025-05-14 23:43:16.34378	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1195	2025-05-14 23:44:31.173963	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1196	2025-05-14 23:45:31.199137	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1197	2025-05-14 23:46:31.213742	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1198	2025-05-14 23:48:31.310419	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1199	2025-05-14 23:50:31.223623	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1200	2025-05-14 23:52:31.344204	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1201	2025-05-14 23:53:31.322058	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1202	2025-05-14 23:54:31.270486	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1203	2025-05-14 23:56:31.229579	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1204	2025-05-14 23:58:31.396551	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1205	2025-05-15 00:00:31.372795	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1206	2025-05-15 00:02:31.424279	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1207	2025-05-15 00:04:12.351696	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1208	2025-05-15 00:05:25.865004	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1209	2025-05-15 00:06:19.119961	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1210	2025-05-15 00:06:19.199322	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1211	2025-05-15 00:06:23.004068	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1212	2025-05-15 00:06:33.377586	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1213	2025-05-15 00:07:45.997501	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1214	2025-05-15 00:08:54.931891	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1215	2025-05-15 00:10:16.274707	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1216	2025-05-15 00:11:31.26226	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1217	2025-05-15 00:11:49.851922	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1218	2025-05-15 00:13:16.832088	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1219	2025-05-15 00:13:46.947747	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1220	2025-05-15 00:13:47.02671	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1221	2025-05-15 00:13:50.99336	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1222	2025-05-15 00:13:51.056297	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1223	2025-05-15 00:13:53.187964	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1224	2025-05-15 00:15:17.136524	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1225	2025-05-15 00:16:46.910434	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1226	2025-05-15 00:17:28.945711	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1227	2025-05-15 00:18:32.530618	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1228	2025-05-15 00:19:07.98225	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1229	2025-05-15 00:20:17.07633	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1230	2025-05-15 00:21:17.11973	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1231	2025-05-15 00:22:22.319211	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1232	2025-05-15 00:23:52.23302	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1233	2025-05-15 00:24:52.285199	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1234	2025-05-15 00:26:31.714053	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1235	2025-05-15 00:27:33.917227	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1236	2025-05-15 00:29:31.895372	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1237	2025-05-15 00:30:32.249601	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1238	2025-05-15 00:32:32.522452	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1239	2025-05-15 00:34:31.545644	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1240	2025-05-15 00:35:31.797343	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1241	2025-05-15 00:37:13.223171	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1242	2025-05-15 00:38:21.929013	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1243	2025-05-15 00:39:21.942164	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1244	2025-05-15 00:40:22.11405	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1245	2025-05-15 00:41:52.128038	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1246	2025-05-15 00:42:51.95486	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1247	2025-05-15 00:44:21.958482	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1248	2025-05-15 00:45:21.973445	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1383	2025-05-19 18:09:49.275848	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1249	2025-05-15 00:46:52.080005	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1250	2025-05-15 00:47:52.011991	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1251	2025-05-15 00:49:21.958678	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1252	2025-05-15 00:50:21.975567	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1253	2025-05-15 00:51:22.254619	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1254	2025-05-15 00:52:31.260518	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1255	2025-05-15 00:53:31.302912	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1256	2025-05-15 00:55:31.262686	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1257	2025-05-15 00:57:10.396971	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1258	2025-05-15 01:05:32.192666	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1259	2025-05-15 01:07:31.250081	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1260	2025-05-15 01:08:27.975897	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1261	2025-05-15 01:08:28.043241	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1262	2025-05-15 01:08:31.990962	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1263	2025-05-15 01:08:32.043064	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1264	2025-05-15 01:08:34.208032	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1265	2025-05-15 01:09:55.264856	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1266	2025-05-15 01:11:25.26374	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1267	2025-05-15 01:12:31.288023	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1268	2025-05-15 01:13:31.466592	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1269	2025-05-15 01:15:31.273278	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1270	2025-05-15 01:16:31.296075	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1271	2025-05-15 01:17:54.348824	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1272	2025-05-15 01:18:56.408063	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1273	2025-05-15 01:18:58.480217	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1274	2025-05-15 01:19:04.303158	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1275	2025-05-15 01:19:44.892294	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1384	2025-05-19 18:09:49.369536	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1276	2025-05-15 01:20:24.38778	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1277	2025-05-15 01:20:55.761726	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1278	2025-05-15 01:20:55.826188	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1279	2025-05-15 01:20:59.769691	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1280	2025-05-15 01:20:59.812344	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1281	2025-05-15 01:21:01.96715	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1282	2025-05-15 01:22:31.296997	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1283	2025-05-15 01:24:15.846791	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1284	2025-05-15 01:25:31.316272	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1285	2025-05-15 01:26:31.300227	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1286	2025-05-15 01:27:07.356519	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1287	2025-05-15 01:28:31.325335	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1288	2025-05-15 01:29:31.336647	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1289	2025-05-15 01:31:01.347801	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1290	2025-05-15 01:32:31.442597	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1291	2025-05-15 01:33:31.421913	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1292	2025-05-15 01:35:01.250208	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1293	2025-05-15 01:36:31.333465	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1294	2025-05-15 01:36:52.902674	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1295	2025-05-15 01:38:31.32507	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1296	2025-05-15 01:39:31.388087	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1297	2025-05-15 01:40:09.559818	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1298	2025-05-15 01:41:31.332803	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1299	2025-05-15 01:42:31.314274	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1300	2025-05-15 01:43:31.43592	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1385	2025-05-19 18:09:53.276748	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1301	2025-05-15 01:44:27.242593	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1302	2025-05-15 01:45:31.382297	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1303	2025-05-15 01:47:31.336541	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1304	2025-05-15 01:48:31.33634	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1305	2025-05-15 01:49:31.432138	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1306	2025-05-15 01:50:09.083519	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1307	2025-05-15 01:51:31.399607	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1308	2025-05-15 01:52:31.518752	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1309	2025-05-15 01:53:31.476561	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1310	2025-05-15 01:54:02.271502	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1311	2025-05-15 01:55:31.364412	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1312	2025-05-15 01:57:31.402052	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1313	2025-05-15 01:59:31.463012	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1314	2025-05-15 02:00:31.353495	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1315	2025-05-15 02:00:39.649382	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1316	2025-05-15 02:02:31.373056	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1317	2025-05-15 02:03:31.428977	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1318	2025-05-15 02:05:31.380426	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1319	2025-05-15 02:07:31.38523	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1320	2025-05-15 02:09:31.433917	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1321	2025-05-15 02:11:31.559746	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1322	2025-05-15 02:12:31.529724	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1323	2025-05-15 02:14:31.396873	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1386	2025-05-19 18:10:31.827028	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1324	2025-05-15 02:15:31.44495	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1325	2025-05-15 02:17:31.510266	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1326	2025-05-15 02:19:31.464346	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1327	2025-05-15 02:21:31.394709	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1328	2025-05-15 02:23:31.496233	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1329	2025-05-15 02:24:31.418252	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1330	2025-05-15 02:25:31.49609	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1331	2025-05-15 02:27:31.40188	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1332	2025-05-15 02:28:31.494681	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1333	2025-05-15 02:29:31.3872	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1334	2025-05-15 02:31:31.495776	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1335	2025-05-15 02:33:31.571489	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1336	2025-05-15 02:34:31.542466	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1337	2025-05-19 17:30:47.897125	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1338	2025-05-19 17:30:48.030703	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1339	2025-05-19 17:30:51.886085	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1340	2025-05-19 17:31:30.441596	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1341	2025-05-19 17:31:52.387965	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1342	2025-05-19 17:32:14.501361	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1343	2025-05-19 17:32:14.572783	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1344	2025-05-19 17:32:18.729941	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1345	2025-05-19 17:32:18.900764	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1346	2025-05-19 17:32:20.761307	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1347	2025-05-19 17:32:26.27382	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1348	2025-05-19 17:32:26.358091	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1349	2025-05-19 17:32:30.280836	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1350	2025-05-19 17:32:30.343224	metrics_collection_retry_success	info	system_metrics	unknown	\N	Successfully collected metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1351	2025-05-19 17:32:32.513164	service_restart_success	info	system	unknown	\N	SyncService was successfully restarted after 1 attempt(s)	\N	\N	\N	system	\N	\N	\N
1352	2025-05-19 17:33:34.891428	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1353	2025-05-19 17:35:04.902048	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1354	2025-05-19 17:36:04.992638	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1355	2025-05-19 17:37:04.905098	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1356	2025-05-19 17:38:05.259754	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1357	2025-05-19 17:39:50.456913	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1358	2025-05-19 17:40:49.281529	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1359	2025-05-19 17:42:04.938926	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1360	2025-05-19 17:43:05.061136	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1361	2025-05-19 17:44:34.948398	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1362	2025-05-19 17:46:05.111085	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1363	2025-05-19 17:47:05.286207	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1364	2025-05-19 17:48:05.169529	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1365	2025-05-19 17:49:34.953368	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1366	2025-05-19 17:50:35.341945	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1367	2025-05-19 17:51:34.951339	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1368	2025-05-19 17:52:35.391475	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1369	2025-05-19 17:54:04.986125	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1370	2025-05-19 17:55:35.213694	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1371	2025-05-19 17:57:05.014704	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1372	2025-05-19 17:58:05.994242	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1373	2025-05-19 17:59:49.351156	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1374	2025-05-19 18:01:02.424034	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1375	2025-05-19 18:02:59.240124	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1376	2025-05-19 18:03:59.271649	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1377	2025-05-19 18:04:51.241848	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1378	2025-05-19 18:04:53.329213	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1379	2025-05-19 18:05:39.658351	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1380	2025-05-19 18:05:53.349417	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1381	2025-05-19 18:06:53.299764	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1382	2025-05-19 18:08:53.268775	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1387	2025-05-19 18:10:53.472738	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1388	2025-05-19 18:11:53.304343	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1389	2025-05-19 18:12:53.327296	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1390	2025-05-19 18:14:09.297099	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1391	2025-05-19 18:14:49.291372	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1392	2025-05-19 18:14:49.414853	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1393	2025-05-19 18:15:31.753328	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1394	2025-05-19 18:15:53.415545	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1395	2025-05-19 18:16:53.298448	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1396	2025-05-19 18:17:53.305906	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1397	2025-05-19 18:18:53.388466	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1398	2025-05-19 18:19:49.303734	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1399	2025-05-19 18:19:49.379514	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1400	2025-05-19 18:20:31.751974	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1401	2025-05-19 18:20:53.309682	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1402	2025-05-19 18:21:53.311976	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1403	2025-05-19 18:22:53.318606	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1404	2025-05-19 18:24:49.379879	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1405	2025-05-19 18:24:49.463552	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1406	2025-05-19 18:24:53.948728	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1407	2025-05-19 18:25:32.001591	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1408	2025-05-19 18:26:53.338597	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1409	2025-05-19 18:27:53.340247	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1410	2025-05-19 18:28:53.337505	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1411	2025-05-19 18:29:53.349542	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1412	2025-05-19 18:30:49.540665	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1413	2025-05-19 18:30:49.630798	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1414	2025-05-19 18:30:53.406917	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1415	2025-05-19 18:31:31.94237	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1416	2025-05-19 18:32:53.362245	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1417	2025-05-19 18:34:09.347879	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1418	2025-05-19 18:35:53.369554	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1419	2025-05-19 18:36:30.723054	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1420	2025-05-19 18:36:30.844326	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1421	2025-05-19 18:37:09.365888	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1422	2025-05-19 18:37:13.16185	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1423	2025-05-19 18:38:53.524519	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1424	2025-05-19 18:39:53.388262	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1425	2025-05-19 18:41:49.444904	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1426	2025-05-19 18:41:49.547668	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1427	2025-05-19 18:41:53.444628	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1428	2025-05-19 18:42:31.898884	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1429	2025-05-19 18:43:53.535032	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1430	2025-05-19 18:45:53.402428	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1431	2025-05-19 18:46:53.404628	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1432	2025-05-19 18:47:49.455688	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1433	2025-05-19 18:47:49.522853	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1434	2025-05-19 18:47:53.46418	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1435	2025-05-19 18:48:31.896248	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1436	2025-05-19 18:49:53.599201	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1437	2025-05-19 18:50:53.415372	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1438	2025-05-19 18:51:53.491167	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1439	2025-05-19 18:52:53.433981	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1440	2025-05-19 18:53:49.513736	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1441	2025-05-19 18:53:49.640054	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1442	2025-05-19 18:53:53.489696	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1443	2025-05-19 18:54:32.077313	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1444	2025-05-19 18:55:53.556533	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1445	2025-05-19 18:57:53.447616	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1446	2025-05-19 19:03:46.576539	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1447	2025-05-19 19:03:46.738938	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1448	2025-05-19 19:03:49.474988	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1449	2025-05-21 18:54:33.126987	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1450	2025-05-21 18:54:33.25483	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1451	2025-05-21 18:54:37.133758	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1452	2025-05-21 18:55:15.568771	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1453	2025-05-21 18:55:34.180137	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1454	2025-05-21 18:55:34.248741	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1455	2025-05-21 18:55:38.042749	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1456	2025-05-21 18:56:16.568834	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1457	2025-05-21 18:56:38.041661	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1458	2025-05-21 18:57:46.031089	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1459	2025-05-21 18:58:46.041777	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1460	2025-05-21 18:59:46.083363	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1461	2025-05-21 19:01:17.249241	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1462	2025-05-21 19:01:17.337756	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1463	2025-05-21 19:01:21.121617	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1464	2025-05-21 19:01:59.705808	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1465	2025-05-21 19:02:21.216401	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1466	2025-05-21 19:04:21.053977	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1467	2025-05-21 19:05:21.117988	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1468	2025-05-21 19:07:17.208103	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1469	2025-05-21 19:07:17.272429	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1470	2025-05-21 19:07:21.101708	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1471	2025-05-21 19:07:59.566025	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1472	2025-05-21 19:09:21.026234	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1473	2025-05-21 19:10:21.046226	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1474	2025-05-21 19:11:21.292975	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1475	2025-05-21 19:13:17.112149	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1476	2025-05-21 19:13:17.167593	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1477	2025-05-21 19:13:21.025959	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1478	2025-05-21 19:13:59.467316	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1479	2025-05-21 19:14:21.056535	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1480	2025-05-21 19:16:25.343944	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1481	2025-05-21 19:18:17.245311	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1482	2025-05-21 19:18:17.386463	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1483	2025-05-21 19:18:21.131411	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1484	2025-05-21 19:18:59.73461	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1485	2025-05-21 19:19:21.212966	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1486	2025-05-21 19:21:21.183281	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1487	2025-05-21 19:23:21.205929	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1488	2025-05-21 19:24:17.207592	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1489	2025-05-21 19:24:17.279413	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1490	2025-05-21 19:24:21.11034	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1491	2025-05-21 19:24:59.60829	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1492	2025-05-21 19:25:21.232755	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1493	2025-05-21 19:27:21.014516	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1494	2025-05-21 19:28:21.272875	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1495	2025-05-21 19:30:17.285632	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1496	2025-05-21 19:30:17.352402	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1497	2025-05-21 19:30:21.193817	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1498	2025-05-21 19:30:59.644112	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1499	2025-05-21 19:32:21.049556	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1500	2025-05-21 19:34:21.104709	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1501	2025-05-21 19:35:20.989923	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1502	2025-05-21 19:36:17.149621	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1503	2025-05-21 19:36:17.216326	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1504	2025-05-21 19:36:21.043669	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1505	2025-05-21 19:36:59.549924	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1506	2025-05-21 19:37:21.064403	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1507	2025-05-21 19:39:20.986821	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1508	2025-05-21 19:40:21.002279	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1509	2025-05-21 19:42:16.998617	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1510	2025-05-21 19:42:17.056372	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1511	2025-05-21 19:42:21.027121	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1512	2025-05-21 19:42:59.358434	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1513	2025-05-21 19:43:21.392082	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1514	2025-05-22 21:00:29.962454	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1515	2025-05-22 21:00:30.068527	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1516	2025-05-22 21:00:33.847505	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1517	2025-05-22 21:01:12.413566	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1518	2025-05-22 21:01:34.182999	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1519	2025-05-22 21:02:34.178567	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1520	2025-05-22 21:03:34.202397	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1521	2025-05-22 21:04:37.02043	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1522	2025-05-22 21:05:34.902727	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1523	2025-05-22 21:05:34.98663	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1524	2025-05-22 21:05:38.764058	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1525	2025-05-22 21:06:17.311381	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1526	2025-05-22 21:07:08.692304	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1527	2025-05-22 21:08:08.704528	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1528	2025-05-22 21:09:38.697888	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1529	2025-05-22 21:10:38.79898	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1530	2025-05-22 21:11:04.820912	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1531	2025-05-22 21:11:04.88081	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1532	2025-05-22 21:11:47.29446	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1533	2025-05-22 21:12:08.705684	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1534	2025-05-22 21:13:08.712985	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1535	2025-05-22 21:14:08.72169	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1536	2025-05-22 21:15:08.732912	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1537	2025-05-22 21:16:08.863999	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1538	2025-05-22 21:16:34.818312	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1539	2025-05-22 21:16:34.890047	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1540	2025-05-22 21:17:08.84211	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1541	2025-05-22 21:17:17.203307	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1542	2025-05-22 21:18:38.733508	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1543	2025-05-22 21:20:08.753526	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1544	2025-05-22 21:21:09.882452	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1545	2025-05-22 21:22:05.91206	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1546	2025-05-22 21:22:05.985098	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1547	2025-05-22 21:22:09.804136	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1548	2025-05-22 21:22:48.329537	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1549	2025-05-22 21:24:09.776121	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1550	2025-05-22 21:25:09.77434	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1551	2025-05-22 21:27:09.920239	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1552	2025-05-22 21:28:05.864047	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1553	2025-05-22 21:28:05.927078	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1554	2025-05-22 21:28:09.865239	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1555	2025-05-22 21:28:48.264493	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1556	2025-05-22 21:30:09.903093	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1557	2025-05-22 21:31:44.843525	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1558	2025-05-22 21:33:08.898973	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1559	2025-05-22 21:33:34.785523	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1560	2025-05-22 21:33:34.867727	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1561	2025-05-22 21:34:08.797594	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1562	2025-05-22 21:34:17.172262	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1563	2025-05-22 21:35:38.860619	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1564	2025-05-22 21:37:08.803376	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1565	2025-05-22 21:38:34.978867	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1566	2025-05-22 21:38:35.054664	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1567	2025-05-22 21:38:38.803328	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1568	2025-05-22 21:39:17.393001	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1569	2025-05-22 21:39:38.819071	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1570	2025-05-22 21:40:38.832386	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1571	2025-05-22 21:42:07.964069	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1572	2025-05-22 21:43:09.851031	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1573	2025-05-22 21:44:06.016556	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1574	2025-05-22 21:44:06.094281	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1575	2025-05-22 21:44:09.856694	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1576	2025-05-22 21:44:48.427442	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1577	2025-05-22 21:46:09.857819	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1578	2025-05-22 21:47:09.955415	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1579	2025-05-22 21:49:05.953558	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1580	2025-05-22 21:49:06.016082	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1581	2025-05-22 21:49:09.86345	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1582	2025-05-22 21:49:48.334768	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1583	2025-05-22 21:50:09.861286	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1584	2025-05-22 21:51:09.877323	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1585	2025-05-22 21:52:09.87988	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1586	2025-05-22 21:53:09.936301	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1587	2025-05-22 21:54:05.988038	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1588	2025-05-22 21:54:06.050774	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1589	2025-05-22 21:54:48.368031	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1590	2025-05-22 21:55:08.548256	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1591	2025-05-22 21:56:08.862091	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1592	2025-05-22 21:57:08.873141	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1593	2025-05-22 21:58:20.006568	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1594	2025-05-22 21:59:34.997729	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1595	2025-05-22 21:59:35.060847	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1596	2025-05-22 21:59:38.892991	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1597	2025-05-22 22:00:17.386707	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1598	2025-05-22 22:01:08.884112	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1599	2025-05-22 22:02:08.912857	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1600	2025-05-22 22:03:08.910183	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1601	2025-05-22 22:04:09.963203	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1602	2025-05-22 22:05:06.101974	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1603	2025-05-22 22:05:06.176539	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1604	2025-05-22 22:05:48.488504	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1605	2025-05-22 22:06:10.081713	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1606	2025-05-22 22:08:09.947011	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1607	2025-05-22 22:10:06.061418	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1608	2025-05-22 22:10:06.145541	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1609	2025-05-22 22:10:09.936809	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1610	2025-05-22 22:10:48.442975	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1611	2025-05-22 22:11:09.954925	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1612	2025-05-22 22:12:10.075383	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1613	2025-05-22 22:14:09.95746	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1614	2025-05-22 22:15:06.095701	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1615	2025-05-22 22:15:06.173616	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1616	2025-05-22 22:15:09.959725	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1617	2025-05-22 22:15:48.487429	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1618	2025-05-22 22:17:09.979998	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1619	2025-05-22 22:18:10.035292	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1620	2025-05-22 22:19:38.975275	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1621	2025-05-22 22:20:35.081607	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1622	2025-05-22 22:20:35.154525	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1623	2025-05-22 22:21:08.957991	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1624	2025-05-22 22:21:17.498818	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1625	2025-05-22 22:22:08.977531	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1626	2025-05-22 22:23:39.03645	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1627	2025-05-22 22:25:08.988151	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1628	2025-05-22 22:25:35.294415	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1629	2025-05-22 22:25:35.360479	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1630	2025-05-22 22:26:08.984658	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1631	2025-05-22 22:26:17.686064	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1632	2025-05-22 22:27:08.994045	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1633	2025-05-22 22:28:09.023079	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1634	2025-05-22 22:29:10.081078	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1635	2025-05-22 22:31:06.154231	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1636	2025-05-22 22:31:06.228083	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1637	2025-05-22 22:31:10.02469	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1638	2025-05-22 22:31:48.524286	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1639	2025-05-22 22:32:39.032966	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1640	2025-05-22 22:34:10.027539	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1641	2025-05-22 22:35:10.085245	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1642	2025-05-22 22:36:06.182305	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1643	2025-05-22 22:36:06.259975	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1644	2025-05-22 22:36:48.596685	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1645	2025-05-22 22:37:10.045674	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1646	2025-05-22 22:38:10.055773	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1647	2025-05-22 22:39:10.059064	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1648	2025-05-22 22:40:10.057902	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1649	2025-05-22 22:41:06.210023	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1650	2025-05-22 22:41:06.27801	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1651	2025-05-22 22:41:10.105961	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1652	2025-05-22 22:41:48.642336	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1653	2025-05-22 22:43:10.066932	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1654	2025-05-22 22:45:10.08792	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1655	2025-05-22 22:46:10.20089	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1656	2025-05-22 22:47:06.14647	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1657	2025-05-22 22:47:06.217153	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1658	2025-05-22 22:47:10.147843	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1659	2025-05-22 22:47:48.515901	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1660	2025-05-22 22:49:10.112861	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1661	2025-05-22 22:51:10.098494	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1662	2025-05-22 22:52:10.189588	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1663	2025-05-22 22:53:06.141837	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1664	2025-05-22 22:53:06.209403	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1665	2025-05-22 22:53:10.146136	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1666	2025-05-22 22:53:48.513251	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1667	2025-05-22 22:55:10.114833	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1668	2025-05-22 22:56:10.123436	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1669	2025-05-22 22:58:10.120288	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1670	2025-05-22 22:59:06.168624	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1671	2025-05-22 22:59:06.244651	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1672	2025-05-22 22:59:10.172727	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1673	2025-05-22 22:59:48.574153	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1674	2025-05-22 23:01:04.356444	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1675	2025-05-22 23:02:09.271316	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1676	2025-05-22 23:03:10.13487	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1677	2025-05-22 23:04:10.136763	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1678	2025-05-22 23:05:06.205317	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1679	2025-05-22 23:05:06.276047	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1680	2025-05-22 23:05:10.208966	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1681	2025-05-22 23:05:48.586967	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1682	2025-05-22 23:07:10.156399	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1683	2025-05-22 23:08:10.300942	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1684	2025-05-22 23:10:10.179852	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1685	2025-05-22 23:11:06.231437	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1686	2025-05-22 23:11:06.327474	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1687	2025-05-22 23:11:10.232207	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1688	2025-05-22 23:11:48.688309	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1689	2025-05-22 23:13:10.284395	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1690	2025-05-22 23:14:10.18744	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1691	2025-05-22 23:16:10.187671	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1692	2025-05-22 23:17:06.239758	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1693	2025-05-22 23:17:06.317574	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1694	2025-05-22 23:17:10.243923	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1695	2025-05-22 23:17:48.659748	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1696	2025-05-22 23:19:10.309887	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1697	2025-05-22 23:20:10.205895	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1698	2025-05-22 23:21:10.216517	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1699	2025-05-22 23:23:06.254754	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1700	2025-05-22 23:23:06.326819	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1701	2025-05-22 23:23:10.257595	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1702	2025-05-22 23:23:48.672082	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1703	2025-05-22 23:25:10.310672	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1704	2025-05-22 23:26:10.230792	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1705	2025-05-22 23:28:10.247151	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1706	2025-05-22 23:29:03.285793	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1707	2025-05-22 23:29:03.357884	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1708	2025-05-22 23:29:10.298548	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1709	2025-05-22 23:29:45.721792	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1710	2025-05-22 23:31:10.321823	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1711	2025-05-22 23:32:10.246111	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1712	2025-05-22 23:33:10.252032	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1713	2025-05-22 23:34:06.253856	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1714	2025-05-22 23:34:06.315473	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1715	2025-05-22 23:34:10.270031	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1716	2025-05-22 23:34:48.677591	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1717	2025-05-22 23:35:10.313233	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1718	2025-05-22 23:36:39.376039	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1719	2025-05-22 23:38:10.274475	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1720	2025-05-22 23:39:06.269816	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1721	2025-05-22 23:39:06.338372	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1722	2025-05-22 23:39:48.694602	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1723	2025-05-22 23:39:54.863497	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1724	2025-05-22 23:41:10.384053	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1725	2025-05-22 23:43:10.283676	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1726	2025-05-22 23:44:06.296279	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1727	2025-05-22 23:44:06.375126	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1728	2025-05-22 23:44:10.29582	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1729	2025-05-22 23:44:48.729249	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1730	2025-05-22 23:45:10.300464	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1731	2025-05-22 23:46:10.3047	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1732	2025-05-22 23:47:10.495222	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1733	2025-05-22 23:49:06.304411	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1734	2025-05-22 23:49:06.602691	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1735	2025-05-22 23:49:10.30714	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1736	2025-05-22 23:49:48.931469	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1737	2025-05-22 23:50:10.322644	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1738	2025-05-22 23:51:10.319311	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1739	2025-05-22 23:53:10.505754	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1740	2025-05-22 23:54:06.328493	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1741	2025-05-22 23:54:06.398494	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1742	2025-05-22 23:54:48.765658	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1743	2025-05-22 23:55:10.340774	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1744	2025-05-22 23:56:10.341301	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1745	2025-05-22 23:57:10.343802	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1746	2025-05-22 23:58:39.491061	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1747	2025-05-22 23:59:06.35057	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1748	2025-05-22 23:59:06.418262	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1749	2025-05-22 23:59:48.751002	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1750	2025-05-23 00:00:10.363598	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1751	2025-05-23 00:01:10.36069	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1752	2025-05-23 00:03:10.356734	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1753	2025-05-23 00:04:06.55385	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1754	2025-05-23 00:04:06.619504	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1755	2025-05-23 00:04:10.434771	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1756	2025-05-23 00:04:48.951231	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1757	2025-05-23 19:00:19.936453	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1758	2025-05-23 19:00:20.045707	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1759	2025-05-23 19:00:23.903317	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1760	2025-05-23 19:01:02.395422	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1761	2025-05-23 19:01:25.385859	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1762	2025-05-23 19:02:55.377744	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1763	2025-05-23 19:04:14.393219	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1764	2025-05-23 19:05:14.495577	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1765	2025-05-23 19:06:10.489957	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1766	2025-05-23 19:06:10.562251	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1767	2025-05-23 19:06:14.492415	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1768	2025-05-23 19:06:52.87688	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1769	2025-05-23 19:08:14.394619	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1770	2025-05-23 19:09:40.406536	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1771	2025-05-23 19:10:40.552923	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1772	2025-05-23 19:11:36.420265	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1773	2025-05-23 19:11:36.494297	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1774	2025-05-23 19:11:40.422354	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1775	2025-05-23 19:12:18.814139	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1776	2025-05-23 19:13:14.42366	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1777	2025-05-23 19:14:14.499706	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1778	2025-05-23 19:16:14.441381	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1779	2025-05-23 19:17:10.586045	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1780	2025-05-23 19:17:10.681796	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1781	2025-05-23 19:17:52.993827	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1782	2025-05-23 19:18:14.448273	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1783	2025-05-23 19:19:14.454753	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1784	2025-05-23 19:20:14.58251	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1785	2025-05-23 19:22:10.448987	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1786	2025-05-23 19:22:10.519753	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1787	2025-05-23 19:22:14.452374	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1788	2025-05-23 19:22:52.82408	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1789	2025-05-23 19:23:14.471162	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1790	2025-05-23 19:24:14.47131	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1791	2025-05-23 19:25:14.47909	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1792	2025-05-23 19:26:14.559939	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1793	2025-05-23 19:27:10.476917	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1794	2025-05-23 19:27:10.544116	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1795	2025-05-23 19:27:52.85693	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1796	2025-05-23 19:28:14.480073	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1797	2025-05-23 19:29:14.486582	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1798	2025-05-23 19:30:14.486818	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1799	2025-05-23 19:31:14.623629	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1800	2025-05-23 19:32:10.699299	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1801	2025-05-23 19:32:10.782344	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1802	2025-05-23 19:32:14.580747	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1803	2025-05-23 19:32:53.119974	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1804	2025-05-23 19:34:14.518031	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1805	2025-05-23 19:36:14.612164	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1806	2025-05-23 19:37:14.508416	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1807	2025-05-23 19:38:10.693227	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1808	2025-05-23 19:38:10.772107	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1809	2025-05-23 19:38:14.597559	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1810	2025-05-23 19:38:53.092904	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1811	2025-05-23 19:40:14.52395	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1812	2025-05-23 19:41:14.534984	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1813	2025-05-23 19:43:14.533518	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1814	2025-05-23 19:44:10.761085	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1815	2025-05-23 19:44:10.837519	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1816	2025-05-23 19:44:14.614546	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1817	2025-05-23 19:44:53.161767	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1818	2025-05-23 19:46:14.55056	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1819	2025-05-23 19:48:08.467829	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1820	2025-05-23 19:49:10.288503	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1821	2025-05-23 19:49:36.729495	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1822	2025-05-23 19:49:36.801367	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1823	2025-05-23 19:50:10.551767	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1824	2025-05-23 19:50:19.118832	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1825	2025-05-23 19:51:14.555279	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1826	2025-05-23 19:52:10.753382	metrics_collected	info	system_metrics	unknown	\N	Collected system metrics from SyncService (CPU: 0.0%, Memory: 0.0%)	\N	{"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "api_requests": 0, "active_syncs": 0, "active_users": 0, "average_response_time": 0.0, "error_rate": 0.0}	\N	system	\N	\N	\N
1827	2025-05-23 19:54:23.748932	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1828	2025-05-23 19:55:12.618668	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1829	2025-05-23 19:55:14.692671	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1830	2025-05-23 19:55:20.624589	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1831	2025-05-23 19:56:01.065371	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1832	2025-05-23 19:57:14.587558	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1833	2025-05-23 19:58:14.58969	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1834	2025-05-23 20:00:14.734354	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1835	2025-05-23 20:01:10.659294	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1836	2025-05-23 20:01:10.765584	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1837	2025-05-23 20:01:14.661231	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1838	2025-05-23 20:01:53.168294	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1839	2025-05-23 20:03:14.608956	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1840	2025-05-23 20:04:14.61676	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1841	2025-05-23 20:05:14.775245	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1842	2025-05-23 20:07:10.677482	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1843	2025-05-23 20:07:10.759131	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1844	2025-05-23 20:07:14.67746	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1845	2025-05-23 20:07:53.112003	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1846	2025-05-23 21:39:04.392577	service_outage_detected	warning	system	unknown	\N	SyncService outage detected during periodic health check	\N	\N	\N	system	\N	\N	\N
1847	2025-05-23 21:39:04.485699	service_restart_attempt	warning	system	unknown	\N	Automatic SyncService restart triggered due to detected outage	\N	\N	\N	system	\N	\N	\N
1848	2025-05-23 21:39:08.294478	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1849	2025-05-23 21:39:46.818627	service_restart_failure	error	system	unknown	\N	Failed to restart SyncService after 3 attempts	\N	\N	\N	system	\N	\N	\N
1850	2025-05-23 21:40:08.96348	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
1851	2025-05-23 21:41:38.978871	metrics_collection_failed	warning	system_metrics	unknown	\N	Failed to collect metrics after 3 attempts	\N	\N	\N	system	\N	\N	\N
\.


--
-- TOC entry 3632 (class 0 OID 122910)
-- Dependencies: 250
-- Data for Name: audit_entry; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.audit_entry (id, event_type, resource_type, resource_id, operation_id, description, previous_state, new_state, severity, user_id, username, ip_address, created_at, correlation_id) FROM stdin;
1	sync_started	sync_pair	1	\N	Sync operation started for PACS-CAMA Integration	\N	\N	info	\N	admin	\N	2025-05-23 19:43:25.164396	\N
2	sync_completed	sync_pair	1	\N	Sync operation completed successfully for PACS-CAMA Integration	\N	\N	info	\N	admin	\N	2025-05-23 19:58:25.164399	\N
\.


--
-- TOC entry 3649 (class 0 OID 147456)
-- Dependencies: 267
-- Data for Name: compliance_audit_logs; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.compliance_audit_logs (id, operation_id, record_type, record_id, operation_type, source_system, ai_model_version, confidence_score, user_id, "timestamp", data_hash, change_summary, compliance_flags, review_required, reviewed_by, reviewed_at, review_notes) FROM stdin;
\.


--
-- TOC entry 3638 (class 0 OID 131116)
-- Dependencies: 256
-- Data for Name: counties; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.counties (id, county_id, name, state, config_path, created_at, updated_at) FROM stdin;
1	benton-wa	Benton County	WA	county_configs/benton-wa/	2025-05-24 02:28:36.007826	2025-05-24 02:28:36.007829
2	king-wa	King County	WA	county_configs/king-wa/	2025-05-24 02:28:36.048029	2025-05-24 02:28:36.048032
3	pierce-wa	Pierce County	WA	county_configs/pierce-wa/	2025-05-24 02:28:36.09142	2025-05-24 02:28:36.091424
4	snohomish-wa	Snohomish County	WA	county_configs/snohomish-wa/	2025-05-24 02:28:36.127473	2025-05-24 02:28:36.127477
\.


--
-- TOC entry 3628 (class 0 OID 122890)
-- Dependencies: 246
-- Data for Name: gis_export_job; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.gis_export_job (id, job_id, county_id, username, export_format, area_of_interest, layers, status, created_at, started_at, completed_at, download_url, result_file_location, result_file_size_kb, result_record_count, message, updated_at) FROM stdin;
1	abc123	benton-wa	admin	geojson	{"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}	["parcels", "buildings"]	COMPLETED	2025-05-23 20:43:25.164328	2025-05-23 20:48:25.164336	2025-05-23 20:53:25.164338	/api/v1/gis-export/download/abc123	\N	\N	\N	Export completed successfully	2025-05-23 21:43:25.183802
\.


--
-- TOC entry 3640 (class 0 OID 131125)
-- Dependencies: 258
-- Data for Name: gis_export_jobs; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.gis_export_jobs (id, job_id, county_id, user_id, username, export_format, area_of_interest, layers, parameters, status, message, file_path, file_size, download_url, created_at, started_at, completed_at) FROM stdin;
1	e45d48a0-18a8-47c5-ab02-bd24b0aba2e5	benton-wa	\N	admin@benton.wa.gov	geojson	{"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}	["parcels", "buildings", "roads"]	{}	COMPLETED	Export completed successfully with 3 layers.	exports/benton-wa_e45d48a0-18a8-47c5-ab02-bd24b0aba2e5.geojson	2622	/api/v1/gis-export/download/e45d48a0-18a8-47c5-ab02-bd24b0aba2e5	2025-05-23 21:51:06.370278	2025-05-23 21:51:06.371285	2025-05-23 21:51:06.372095
2	1fb39635-7319-4af0-8c2d-916608e4081b	benton-wa	\N	county-admin	geojson	{"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}	["parcels", "buildings", "roads"]	{}	COMPLETED	Export completed successfully with 3 layers.	exports/benton-wa_1fb39635-7319-4af0-8c2d-916608e4081b.geojson	2615	/api/v1/gis-export/download/1fb39635-7319-4af0-8c2d-916608e4081b	2025-05-23 21:52:27.811082	2025-05-23 21:52:27.811666	2025-05-23 21:52:27.812875
\.


--
-- TOC entry 3619 (class 0 OID 81967)
-- Dependencies: 237
-- Data for Name: import_jobs; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.import_jobs (id, source_system_id, job_type, status, total_records, processed_records, successful_records, failed_records, start_time, end_time, estimated_completion_time, job_parameters, result_summary, error_log, created_at, created_by) FROM stdin;
\.


--
-- TOC entry 3623 (class 0 OID 90112)
-- Dependencies: 241
-- Data for Name: market_analysis_jobs; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.market_analysis_jobs (job_id, analysis_type, county_id, status, message, parameters_json, created_at, updated_at, started_at, completed_at, result_summary_json, result_data_location) FROM stdin;
cff1b41e-aba5-415b-b0ea-e68947d50b71	price_trend_by_zip	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 19:43:41.062534	2025-05-12 19:43:41.062537	\N	\N	\N	\N
7d721083-006c-41a0-bc09-8c64e8ca4c87	comparable_market_area	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"reference_zip": "90210", "max_distance_miles": 25, "property_types": ["residential", "commercial"]}	2025-05-12 19:43:42.817102	2025-05-12 19:43:42.817107	\N	\N	\N	\N
13c0df2f-ab84-4218-96aa-78a2042c47bd	sales_velocity	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"start_date": "2024-01-01", "end_date": "2024-12-31", "area_codes": ["90210", "90211", "90212"]}	2025-05-12 19:43:44.686407	2025-05-12 19:43:44.68641	\N	\N	\N	\N
4dd7dca8-f2e4-41e8-8ab4-1e55b30bdbb8	market_valuation	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"area_code": "90210", "property_type": "residential", "min_sqft": 1000, "max_sqft": 3000}	2025-05-12 19:43:46.224754	2025-05-12 19:43:46.224757	\N	\N	\N	\N
4df8e007-a7bd-40e6-b6c9-6b69d2c0a9f2	price_per_sqft	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"area_codes": ["90210", "90211"], "property_types": ["residential", "commercial"], "start_date": "2024-01-01", "end_date": "2024-12-31"}	2025-05-12 19:43:47.582139	2025-05-12 19:43:47.582142	\N	\N	\N	\N
0c99f071-d3b1-4eaf-bdcf-69f08ad5e97e	price_trend_by_zip	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 19:45:28.182463	2025-05-12 19:45:28.182466	\N	\N	\N	\N
bb1c7d41-9bfa-4e7d-9727-74f88c9b811b	comparable_market_area	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"reference_zip": "90210", "max_distance_miles": 25, "property_types": ["residential", "commercial"]}	2025-05-12 19:45:29.67132	2025-05-12 19:45:29.671324	\N	\N	\N	\N
b226cd3c-a5c9-4cb2-9db8-d42b405ff8d6	sales_velocity	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"start_date": "2024-01-01", "end_date": "2024-12-31", "area_codes": ["90210", "90211", "90212"]}	2025-05-12 19:45:31.230623	2025-05-12 19:45:31.230625	\N	\N	\N	\N
dfda1db7-f327-4972-bbea-5742a29a58c6	market_valuation	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"area_code": "90210", "property_type": "residential", "min_sqft": 1000, "max_sqft": 3000}	2025-05-12 19:45:32.604959	2025-05-12 19:45:32.604962	\N	\N	\N	\N
df89966a-9269-4d8b-8db5-e3af73f72396	price_per_sqft	TEST_COUNTY	PENDING	Market analysis job accepted and queued	{"area_codes": ["90210", "90211"], "property_types": ["residential", "commercial"], "start_date": "2024-01-01", "end_date": "2024-12-31"}	2025-05-12 19:45:33.985403	2025-05-12 19:45:33.985406	\N	\N	\N	\N
77b1508b-2355-4250-9c0e-0b5fdfdf1da9	price_trend_by_zip	TEST_COUNTY	COMPLETED	Analysis completed successfully	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 19:55:36.175008	2025-05-12 19:55:39.775647	2025-05-12 19:55:36.631418	2025-05-12 19:55:39.775644	{"key_finding": "Market prices increased by 5% year-over-year", "data_points_analyzed": 8, "recommendation": "Market conditions favorable for revaluation", "analyzed_zip_codes": ["90210", "90211"]}	/data/analysis_results/TEST_COUNTY/price_trend_by_zip/77b1508b-2355-4250-9c0e-0b5fdfdf1da9.parquet
961db893-6fa6-4a18-a0a1-676b77e81b82	comparable_market_area	TEST_COUNTY	COMPLETED	Analysis completed successfully	{"reference_zip": "90210", "max_distance_miles": 25, "property_types": ["residential", "commercial"]}	2025-05-12 19:55:37.935738	2025-05-12 19:55:41.696436	2025-05-12 19:55:38.386012	2025-05-12 19:55:41.696435	{}	/data/analysis_results/TEST_COUNTY/comparable_market_area/961db893-6fa6-4a18-a0a1-676b77e81b82.parquet
15e37564-103e-431b-a0a3-c4c4e1c92042	sales_velocity	TEST_COUNTY	COMPLETED	Analysis completed successfully	{"start_date": "2024-01-01", "end_date": "2024-12-31", "area_codes": ["90210", "90211", "90212"]}	2025-05-12 19:55:39.512619	2025-05-12 19:55:42.990028	2025-05-12 19:55:39.812824	2025-05-12 19:55:42.990026	{}	/data/analysis_results/TEST_COUNTY/sales_velocity/15e37564-103e-431b-a0a3-c4c4e1c92042.parquet
73ddd2e7-db24-403c-9d9d-83e278c5775e	market_valuation	TEST_COUNTY	COMPLETED	Analysis completed successfully	{"area_code": "90210", "property_type": "residential", "min_sqft": 1000, "max_sqft": 3000}	2025-05-12 19:55:41.261383	2025-05-12 19:55:44.829111	2025-05-12 19:55:41.585769	2025-05-12 19:55:44.829109	{}	/data/analysis_results/TEST_COUNTY/market_valuation/73ddd2e7-db24-403c-9d9d-83e278c5775e.parquet
1f5bba5f-3ec7-43f7-aec2-cd27380b279c	price_per_sqft	TEST_COUNTY	COMPLETED	Analysis completed successfully	{"area_codes": ["90210", "90211"], "property_types": ["residential", "commercial"], "start_date": "2024-01-01", "end_date": "2024-12-31"}	2025-05-12 19:55:42.727547	2025-05-12 19:55:46.203869	2025-05-12 19:55:43.091307	2025-05-12 19:55:46.203867	{}	/data/analysis_results/TEST_COUNTY/price_per_sqft/1f5bba5f-3ec7-43f7-aec2-cd27380b279c.parquet
5ca8e40e-84cf-4d68-9378-f2ecc1b44229	price_trend_by_zip	TEST_COUNTY_82928370	COMPLETED	Analysis completed successfully	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 21:44:01.901813	2025-05-12 21:44:05.373001	2025-05-12 21:44:02.240879	2025-05-12 21:44:05.372997	{"key_finding": "Market prices increased by 5% year-over-year", "data_points_analyzed": 8, "recommendation": "Market conditions favorable for revaluation", "analyzed_zip_codes": ["90210", "90211"]}	/data/analysis_results/TEST_COUNTY_82928370/price_trend_by_zip/5ca8e40e-84cf-4d68-9378-f2ecc1b44229.parquet
db8eebbf-56ca-46a0-9674-77e8ac834ad6	price_trend_by_zip	TEST_COUNTY_509ab7fb	COMPLETED	Analysis completed successfully	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 21:44:24.799154	2025-05-12 21:44:28.311332	2025-05-12 21:44:25.17484	2025-05-12 21:44:28.311329	{"key_finding": "Market prices increased by 5% year-over-year", "data_points_analyzed": 8, "recommendation": "Market conditions favorable for revaluation", "analyzed_zip_codes": ["90210", "90211"], "trends": [{"period": "2024-Q1", "average_price": 450000, "median_price": 425000, "sales_volume": 125, "price_per_sqft": 350.0}, {"period": "2024-Q2", "average_price": 462500, "median_price": 435000, "sales_volume": 120, "price_per_sqft": 355.5}, {"period": "2024-Q3", "average_price": 475000, "median_price": 445000, "sales_volume": 115, "price_per_sqft": 361.0}, {"period": "2024-Q4", "average_price": 487500, "median_price": 455000, "sales_volume": 110, "price_per_sqft": 366.5}]}	/data/analysis_results/TEST_COUNTY_509ab7fb/price_trend_by_zip/db8eebbf-56ca-46a0-9674-77e8ac834ad6.parquet
7c287d3d-4040-4965-8808-e439084f3aa7	price_trend_by_zip	TEST_COUNTY_55f2275b	COMPLETED	Analysis completed successfully	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 21:44:49.175677	2025-05-12 21:44:52.576331	2025-05-12 21:44:49.466484	2025-05-12 21:44:52.576328	{"key_finding": "Market prices increased by 5% year-over-year", "data_points_analyzed": 8, "recommendation": "Market conditions favorable for revaluation", "analyzed_zip_codes": ["90210", "90211"], "trends": [{"zip_code": "90210", "data_points": [{"period": "2024-Q1", "average_price": 450000, "median_price": 425000, "sales_volume": 125, "price_per_sqft": 350.0}, {"period": "2024-Q2", "average_price": 462500, "median_price": 435000, "sales_volume": 120, "price_per_sqft": 355.5}, {"period": "2024-Q3", "average_price": 475000, "median_price": 445000, "sales_volume": 115, "price_per_sqft": 361.0}, {"period": "2024-Q4", "average_price": 487500, "median_price": 455000, "sales_volume": 110, "price_per_sqft": 366.5}]}, {"zip_code": "90211", "data_points": [{"period": "2024-Q1", "average_price": 450000, "median_price": 425000, "sales_volume": 125, "price_per_sqft": 350.0}, {"period": "2024-Q2", "average_price": 462500, "median_price": 435000, "sales_volume": 120, "price_per_sqft": 355.5}, {"period": "2024-Q3", "average_price": 475000, "median_price": 445000, "sales_volume": 115, "price_per_sqft": 361.0}, {"period": "2024-Q4", "average_price": 487500, "median_price": 455000, "sales_volume": 110, "price_per_sqft": 366.5}]}]}	/data/analysis_results/TEST_COUNTY_55f2275b/price_trend_by_zip/7c287d3d-4040-4965-8808-e439084f3aa7.parquet
a5687da7-a35d-46b2-8e14-990aab7ce337	price_trend_by_zip	TEST_COUNTY_293bbb17	COMPLETED	Analysis completed successfully	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 21:50:18.882299	2025-05-12 21:50:22.70128	2025-05-12 21:50:19.558293	2025-05-12 21:50:22.701277	{"key_finding": "Market prices increased by 5% year-over-year", "data_points_analyzed": 8, "recommendation": "Market conditions favorable for revaluation", "analyzed_zip_codes": ["90210", "90211"], "trends": [{"period": "2024-Q1", "average_price": 450000, "median_price": 425000, "sales_volume": 125, "price_per_sqft": 350.0}, {"period": "2024-Q2", "average_price": 462500, "median_price": 435000, "sales_volume": 120, "price_per_sqft": 355.5}, {"period": "2024-Q3", "average_price": 475000, "median_price": 445000, "sales_volume": 115, "price_per_sqft": 361.0}, {"period": "2024-Q4", "average_price": 487500, "median_price": 455000, "sales_volume": 110, "price_per_sqft": 366.5}]}	/data/analysis_results/TEST_COUNTY_293bbb17/price_trend_by_zip/a5687da7-a35d-46b2-8e14-990aab7ce337.parquet
e2437e3d-3a85-4a77-a226-f07ae45a8bf5	FAILING_ANALYSIS_SIM	TEST_COUNTY_293bbb17	PENDING	Market analysis job accepted and queued	{"start_date": "2024-01-01", "end_date": "2024-12-31", "property_types": ["residential"]}	2025-05-12 21:50:23.121572	2025-05-12 21:50:23.121575	\N	\N	\N	\N
58cb2393-52ec-448a-ab39-cd0bea4fb14d	price_trend_by_zip	TEST_COUNTY_0485e0de	COMPLETED	Analysis completed successfully	{"start_date": "2024-01-01", "end_date": "2024-12-31", "zip_codes": ["90210", "90211"], "property_types": ["residential"]}	2025-05-12 21:52:47.942634	2025-05-12 21:52:51.347019	2025-05-12 21:52:48.228854	2025-05-12 21:52:51.347016	{"key_finding": "Market prices increased by 5% year-over-year", "data_points_analyzed": 8, "recommendation": "Market conditions favorable for revaluation", "analyzed_zip_codes": ["90210", "90211"], "trends": [{"period": "2024-Q1", "average_price": 450000, "median_price": 425000, "sales_volume": 125, "price_per_sqft": 350.0}, {"period": "2024-Q2", "average_price": 462500, "median_price": 435000, "sales_volume": 120, "price_per_sqft": 355.5}, {"period": "2024-Q3", "average_price": 475000, "median_price": 445000, "sales_volume": 115, "price_per_sqft": 361.0}, {"period": "2024-Q4", "average_price": 487500, "median_price": 455000, "sales_volume": 110, "price_per_sqft": 366.5}]}	/data/analysis_results/TEST_COUNTY_0485e0de/price_trend_by_zip/58cb2393-52ec-448a-ab39-cd0bea4fb14d.parquet
ea43a27b-7b23-45cc-a943-accd8fd0d719	FAILING_ANALYSIS_SIM	TEST_COUNTY_0485e0de	FAILED	Simulated market analysis failure for testing purposes	{"start_date": "2024-01-01", "end_date": "2024-12-31", "property_types": ["residential"]}	2025-05-12 21:52:51.707587	2025-05-12 21:52:52.073251	\N	2025-05-12 21:52:52.071468	\N	\N
3c9faee6-68d3-4425-bafe-cf203cba4523	price_trend_by_zip	SAMPLE_COUNTY	COMPLETED	Analysis completed successfully	{"zip_codes": ["90210", "90211", "90212"], "start_date": "2024-01-01", "end_date": "2024-12-31"}	2025-05-12 22:01:30.137519	2025-05-12 22:01:34.135787	2025-05-12 22:01:31.00849	2025-05-12 22:01:34.135783	{"key_finding": "Market prices increased by 5% year-over-year", "data_points_analyzed": 12, "recommendation": "Market conditions favorable for revaluation", "analyzed_zip_codes": ["90210", "90211", "90212"], "trends": [{"period": "2024-Q1", "average_price": 450000, "median_price": 425000, "sales_volume": 125, "price_per_sqft": 350.0}, {"period": "2024-Q2", "average_price": 462500, "median_price": 435000, "sales_volume": 120, "price_per_sqft": 355.5}, {"period": "2024-Q3", "average_price": 475000, "median_price": 445000, "sales_volume": 115, "price_per_sqft": 361.0}, {"period": "2024-Q4", "average_price": 487500, "median_price": 455000, "sales_volume": 110, "price_per_sqft": 366.5}]}	/data/analysis_results/SAMPLE_COUNTY/price_trend_by_zip/3c9faee6-68d3-4425-bafe-cf203cba4523.parquet
299af36b-fbde-4107-8bfb-5fdf6530c6cf	FAILING_ANALYSIS_SIM	SAMPLE_COUNTY	FAILED	Simulated market analysis failure for testing purposes	{"should_fail": true}	2025-05-12 22:01:44.020168	2025-05-12 22:01:45.220552	\N	2025-05-12 22:01:45.219277	\N	\N
\.


--
-- TOC entry 3610 (class 0 OID 73729)
-- Dependencies: 228
-- Data for Name: onboarding_event; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.onboarding_event (id, user_onboarding_id, event_type, step_id, "timestamp", event_data) FROM stdin;
\.


--
-- TOC entry 3602 (class 0 OID 65601)
-- Dependencies: 220
-- Data for Name: onboarding_events; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.onboarding_events (id, user_id, event_type, step_number, event_data, "timestamp") FROM stdin;
\.


--
-- TOC entry 3611 (class 0 OID 81920)
-- Dependencies: 229
-- Data for Name: properties_operational; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.properties_operational (property_id, county_id, parcel_number, address_street, address_city, address_state, address_zip, property_type, land_area_sqft, building_area_sqft, year_built, bedrooms, bathrooms, last_sale_date, last_sale_price, current_market_value, assessed_value, assessment_year, tax_district, millage_rate, tax_amount, owner_name, owner_type, latitude, longitude, legal_description, is_exempt, exemption_type, is_historical, created_at, updated_at, last_sync_id, data_source, extended_attributes) FROM stdin;
PROP-47180d86	DEMO-001	P-930308	2253 Sample Rd	Sample City	SC	66817	industrial	2855	3552	2008	\N	\N	2019-01-24 18:45:18.242387	710345	917933	531763	2024	Sample District	40.863394029444464	6907	Sample Owner 0	trust	33.0653680400438	-80.77064436484102	Sample legal description for property PROP-47180d86	f	Homestead	f	2025-05-09 18:45:18.336628	2025-05-09 18:45:18.336632	\N	seed-data	{"seed_source": "terrafusion_sync", "generator_version": "0.1.0", "random_attributes": {"attr1": 41, "attr2": "ZjlOqDFq"}}
PROP-c1da39a7	DEMO-001	P-672446	5050 Sample Rd	Sample City	SC	97099	residential	13833	1527	1972	6	2	2023-09-10 18:45:18.266695	633784	813620	410983	2023	Sample District	22.619745591705186	14109	Sample Owner 1	individual	34.2874037045226	-80.8017891892002	Sample legal description for property PROP-c1da39a7	t	Homestead	f	2025-05-09 18:45:18.336632	2025-05-09 18:45:18.336633	\N	seed-data	{"seed_source": "terrafusion_sync", "generator_version": "0.1.0", "random_attributes": {"attr1": 33, "attr2": "blcqnaXf"}}
PROP-599c76d3	DEMO-001	P-991592	2038 Sample St	Sample City	SC	55421	commercial	5631	4122	2001	\N	\N	2018-03-26 18:45:18.26688	241657	639064	785376	2023	Sample District	20.825198456138907	6179	Sample Owner 2	trust	32.1800986539088	-80.1147232436599	Sample legal description for property PROP-599c76d3	t	\N	f	2025-05-09 18:45:18.336634	2025-05-09 18:45:18.336636	\N	seed-data	{"seed_source": "terrafusion_sync", "generator_version": "0.1.0", "random_attributes": {"attr1": 57, "attr2": "lZuIvpZj"}}
PROP-1e5bc8b4	DEMO-001	P-967609	1863 Sample St	Sample City	SC	10680	residential	7804	3380	2001	2	4	2015-08-07 18:45:18.267045	479628	653833	366987	2023	Sample District	29.30320328798751	13435	Sample Owner 3	business	34.91655559912118	-79.44848019069859	Sample legal description for property PROP-1e5bc8b4	f	Homestead	f	2025-05-09 18:45:18.336637	2025-05-09 18:45:18.336638	\N	seed-data	{"seed_source": "terrafusion_sync", "generator_version": "0.1.0", "random_attributes": {"attr1": 20, "attr2": "lkcrjLHB"}}
PROP-f1fd13f0	DEMO-001	P-251004	5037 Sample St	Sample City	SC	54494	vacant	8356	\N	\N	\N	\N	2015-10-09 18:45:18.26728	836580	1059733	582501	2022	Sample District	45.119834732627226	6339	Sample Owner 4	individual	32.05614680234191	-79.99317742639515	Sample legal description for property PROP-f1fd13f0	t	Homestead	f	2025-05-09 18:45:18.336638	2025-05-09 18:45:18.336639	\N	seed-data	{"seed_source": "terrafusion_sync", "generator_version": "0.1.0", "random_attributes": {"attr1": 82, "attr2": "QxkwJdYg"}}
\.


--
-- TOC entry 3617 (class 0 OID 81953)
-- Dependencies: 235
-- Data for Name: property_improvements; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.property_improvements (id, property_id, improvement_type, description, year_completed, area_added_sqft, cost, value_added, permit_number, permit_date, permit_status, created_at, updated_at, data_source) FROM stdin;
\.


--
-- TOC entry 3621 (class 0 OID 81993)
-- Dependencies: 239
-- Data for Name: property_operational; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.property_operational (property_id, county_id, parcel_number, address_street, address_city, address_state, address_zip, property_type, land_area_sqft, building_area_sqft, year_built, bedrooms, bathrooms, last_sale_date, last_sale_price, current_market_value, assessed_value, assessment_year, tax_district, millage_rate, tax_amount, owner_name, owner_type, latitude, longitude, legal_description, is_exempt, exemption_type, is_historical, created_at, updated_at, last_sync_id, data_source, extended_attributes) FROM stdin;
\.


--
-- TOC entry 3615 (class 0 OID 81939)
-- Dependencies: 233
-- Data for Name: property_valuations; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.property_valuations (id, property_id, valuation_date, valuation_amount, valuation_method, valuation_type, valuation_year, confidence_score, margin_of_error, comparables_used, adjustments, notes, is_final, approved_by, approved_at, created_at, created_by, sync_operation_id) FROM stdin;
\.


--
-- TOC entry 3646 (class 0 OID 139282)
-- Dependencies: 264
-- Data for Name: rbac_audit_log; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.rbac_audit_log (id, action_type, target_user_id, target_username, admin_user_id, admin_username, details, "timestamp", ip_address) FROM stdin;
\.


--
-- TOC entry 3648 (class 0 OID 139292)
-- Dependencies: 266
-- Data for Name: rbac_sessions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.rbac_sessions (id, user_id, session_token, jwt_token, created_at, expires_at, is_active, ip_address, user_agent) FROM stdin;
\.


--
-- TOC entry 3644 (class 0 OID 139265)
-- Dependencies: 262
-- Data for Name: rbac_users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.rbac_users (id, username, email, password_hash, role, county_id, is_active, created_at, updated_at, last_login) FROM stdin;
\.


--
-- TOC entry 3622 (class 0 OID 82002)
-- Dependencies: 240
-- Data for Name: report_job; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.report_job (report_id, report_type, county_id, status, message, parameters_json, created_at, updated_at, started_at, completed_at, result_location, result_metadata_json) FROM stdin;
6b02416c-c5f3-44a2-a391-4e846e15eb98	assessment_roll	test_county	PENDING	\N	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 20:51:21.358673	2025-05-09 20:51:21.358676	\N	\N	\N	\N
23983e89-06ef-4ff5-9523-149bbd156ef3	assessment_roll	test_county	PENDING	\N	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 20:52:03.681538	2025-05-09 20:52:03.681541	\N	\N	\N	\N
a4b8ba08-6fa4-4560-9cce-f636052d32be	assessment_roll	test_county	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:14:23.81833	2025-05-09 21:14:24.259818	2025-05-09 21:14:24.205117	2025-05-09 21:14:24.259819	s3://terrafusion-reports/test_county/assessment_roll/a4b8ba08-6fa4-4560-9cce-f636052d32be.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.4794222632862889, "generated_at": "2025-05-09T21:14:24.259807"}
a2f04411-f382-402a-baa5-9d5d623742b5	assessment_roll	test_county	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2}	2025-05-09 21:14:40.786046	2025-05-09 21:14:41.129367	2025-05-09 21:14:41.08706	2025-05-09 21:14:41.129369	s3://terrafusion-reports/test_county/assessment_roll/a2f04411-f382-402a-baa5-9d5d623742b5.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.2489894964228467, "generated_at": "2025-05-09T21:14:41.129359"}
4398698f-ceea-4482-8143-a36041250941	assessment_roll	test_county_1	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2}	2025-05-09 21:14:54.183273	2025-05-09 21:14:54.590611	2025-05-09 21:14:54.552516	2025-05-09 21:14:54.590613	s3://terrafusion-reports/test_county_1/assessment_roll/4398698f-ceea-4482-8143-a36041250941.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.39201476249986633, "generated_at": "2025-05-09T21:14:54.590600"}
90e3367c-ca08-43d8-858b-3588b4664dfb	assessment_roll	test_county_0	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2}	2025-05-09 21:14:54.182463	2025-05-09 21:14:54.6764	2025-05-09 21:14:54.623383	2025-05-09 21:14:54.676402	s3://terrafusion-reports/test_county_0/assessment_roll/90e3367c-ca08-43d8-858b-3588b4664dfb.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.3067517334978782, "generated_at": "2025-05-09T21:14:54.676389"}
1030eb1c-f384-4cc3-a922-30009f7fce7d	assessment_roll	test_county_2	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2}	2025-05-09 21:14:54.184384	2025-05-09 21:14:54.848035	2025-05-09 21:14:54.788955	2025-05-09 21:14:54.848036	s3://terrafusion-reports/test_county_2/assessment_roll/1030eb1c-f384-4cc3-a922-30009f7fce7d.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.4922516860083621, "generated_at": "2025-05-09T21:14:54.848027"}
60ac73e2-d7b1-413f-a86e-2e000fedd840	assessment_roll	test_county_3	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2}	2025-05-09 21:14:54.335868	2025-05-09 21:14:54.947711	2025-05-09 21:14:54.889401	2025-05-09 21:14:54.947712	s3://terrafusion-reports/test_county_3/assessment_roll/60ac73e2-d7b1-413f-a86e-2e000fedd840.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.20214163954792616, "generated_at": "2025-05-09T21:14:54.947705"}
deb816ff-5e1b-496f-a718-1995e5329302	assessment_roll	test_county_4	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2}	2025-05-09 21:14:54.343317	2025-05-09 21:14:54.981165	2025-05-09 21:14:54.94353	2025-05-09 21:14:54.981166	s3://terrafusion-reports/test_county_4/assessment_roll/deb816ff-5e1b-496f-a718-1995e5329302.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.3560681739992625, "generated_at": "2025-05-09T21:14:54.981158"}
92b49c63-3da6-44c6-a3ec-79f0d2111595	assessment_roll	county_1	PENDING	Reset by test	{"year": 2025, "quarter": 2}	2025-05-09 21:16:54.472925	2025-05-09 21:16:55.763207	2025-05-09 21:16:54.79208	2025-05-09 21:16:54.827357	s3://terrafusion-reports/county_1/assessment_roll/92b49c63-3da6-44c6-a3ec-79f0d2111595.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.39259886500281893, "generated_at": "2025-05-09T21:16:54.827345"}
5fc86649-bc39-4bb7-98c2-76e235da5df9	assessment_roll	test_county_tx	PENDING	Reset for testing	{"year": 2025, "quarter": 2}	2025-05-09 21:16:18.583412	2025-05-09 21:16:19.486068	2025-05-09 21:16:19.006436	2025-05-09 21:16:19.098971	s3://terrafusion-reports/test_county_tx/assessment_roll/5fc86649-bc39-4bb7-98c2-76e235da5df9.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.3343621176199273, "generated_at": "2025-05-09T21:16:19.098961"}
8be96455-7354-47ba-9a2d-634da73bc3ca	assessment_roll	county_0	PENDING	Reset by test	{"year": 2025, "quarter": 2}	2025-05-09 21:16:53.509474	2025-05-09 21:16:55.746943	2025-05-09 21:16:54.176929	2025-05-09 21:16:54.230306	s3://terrafusion-reports/county_0/assessment_roll/8be96455-7354-47ba-9a2d-634da73bc3ca.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.2811360618235319, "generated_at": "2025-05-09T21:16:54.230294"}
c3673064-e96c-4c8e-9fbe-ee9746782ac6	assessment_roll	county_2	PENDING	Reset by test	{"year": 2025, "quarter": 2}	2025-05-09 21:16:55.068056	2025-05-09 21:16:55.788848	2025-05-09 21:16:55.393833	2025-05-09 21:16:55.427286	s3://terrafusion-reports/county_2/assessment_roll/c3673064-e96c-4c8e-9fbe-ee9746782ac6.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.2867019295857425, "generated_at": "2025-05-09T21:16:55.427276"}
615ba059-6a6d-488d-b724-1c2774212aec	assessment_roll	TEST_COUNTY_1fb683cf	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:23:36.45276	2025-05-09 21:23:36.853575	2025-05-09 21:23:36.803902	2025-05-09 21:23:36.853577	s3://terrafusion-reports/TEST_COUNTY_1fb683cf/assessment_roll/615ba059-6a6d-488d-b724-1c2774212aec.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.2206203066351485, "generated_at": "2025-05-09T21:23:36.853564"}
953ba875-de19-4445-8177-1e47e58b6b23	assessment_roll	TEST_COUNTY_eab65b95	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:24:42.687798	2025-05-09 21:24:43.210793	2025-05-09 21:24:43.156399	2025-05-09 21:24:43.210794	s3://terrafusion-reports/TEST_COUNTY_eab65b95/assessment_roll/953ba875-de19-4445-8177-1e47e58b6b23.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.3964914262867879, "generated_at": "2025-05-09T21:24:43.210759"}
64de68e5-af5a-4d80-87ae-615aea25c957	assessment_roll	TEST_COUNTY_b302e506	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:26:25.129914	2025-05-09 21:26:25.659104	2025-05-09 21:26:25.602756	2025-05-09 21:26:25.659105	s3://terrafusion-reports/TEST_COUNTY_b302e506/assessment_roll/64de68e5-af5a-4d80-87ae-615aea25c957.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.2924451554116686, "generated_at": "2025-05-09T21:26:25.659095"}
510a7abd-66c7-4c48-ac15-9f7653badd1a	assessment_roll	TEST_COUNTY_1771269d	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:27:19.490483	2025-05-09 21:27:20.157845	2025-05-09 21:27:20.029752	2025-05-09 21:27:20.157847	s3://terrafusion-reports/TEST_COUNTY_1771269d/assessment_roll/510a7abd-66c7-4c48-ac15-9f7653badd1a.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.3919254947931542, "generated_at": "2025-05-09T21:27:20.157832"}
d3103ce6-9bc9-411e-b271-c088fc87dddf	assessment_roll	TEST_COUNTY_22100fab	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:28:32.814284	2025-05-09 21:28:33.242396	2025-05-09 21:28:33.190547	2025-05-09 21:28:33.242397	s3://terrafusion-reports/TEST_COUNTY_22100fab/assessment_roll/d3103ce6-9bc9-411e-b271-c088fc87dddf.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.4050220092132061, "generated_at": "2025-05-09T21:28:33.242386"}
ac1f4001-bc0e-4213-9e17-67ddf7e0eabf	FAILING_REPORT_SIM	TEST_COUNTY_646b9b2f	FAILED	Simulated report generation failure	{"year": 2025, "quarter": 2}	2025-05-09 21:28:34.67393	2025-05-09 21:28:35.01491	2025-05-09 21:28:34.982108	2025-05-09 21:28:35.014912	\N	\N
c8909f8d-610e-4f16-aa64-ff1d7d475ffc	assessment_roll	TEST_COUNTY_bfa8ba57	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:28:59.094288	2025-05-09 21:28:59.791521	2025-05-09 21:28:59.73346	2025-05-09 21:28:59.791522	s3://terrafusion-reports/TEST_COUNTY_bfa8ba57/assessment_roll/c8909f8d-610e-4f16-aa64-ff1d7d475ffc.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.2258792280469216, "generated_at": "2025-05-09T21:28:59.791513"}
7d0cb2ae-bc90-4c54-b677-50ba0b220f53	FAILING_REPORT_SIM	TEST_COUNTY_224913f7	PENDING	\N	{"year": 2025, "quarter": 2}	2025-05-09 21:29:01.283413	2025-05-09 21:29:01.283416	\N	\N	\N	\N
09985e5b-39a0-47d1-8b9b-84ddc9f92871	assessment_roll	TEST_COUNTY_a93dac8b	COMPLETED	Report generation completed successfully	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 21:29:47.111841	2025-05-09 21:29:47.572456	2025-05-09 21:29:47.518752	2025-05-09 21:29:47.572458	s3://terrafusion-reports/TEST_COUNTY_a93dac8b/assessment_roll/09985e5b-39a0-47d1-8b9b-84ddc9f92871.pdf	{"file_size_kb": 1024, "pages": 10, "generation_time_seconds": 0.46497528027688695, "generated_at": "2025-05-09T21:29:47.572446"}
a1dfa59b-272a-4b75-a5eb-f72435797c52	FAILING_REPORT_SIM	TEST_COUNTY_cc7670cc	FAILED	Simulated report generation failure	{"year": 2025, "quarter": 2}	2025-05-09 21:29:48.98887	2025-05-09 21:29:49.297839	2025-05-09 21:29:49.261357	2025-05-09 21:29:49.297843	\N	\N
207cd7ae-fc16-458c-94c5-10cff7818d1f	assessment_roll	TEST_COUNTY_62a4fdac	PENDING	\N	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 22:03:32.451757	2025-05-09 22:03:32.45176	\N	\N	\N	\N
49cc369d-e541-4d0b-86e1-00bdd8840969	assessment_roll	TEST_COUNTY_4349c205	PENDING	\N	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 22:06:23.308989	2025-05-09 22:06:23.308992	\N	\N	\N	\N
ba0a7754-559b-4f0b-9405-59ad1003ce3e	assessment_roll	TEST_COUNTY_A_98a332	PENDING	\N	{"year": 2025}	2025-05-09 22:06:24.680733	2025-05-09 22:06:24.680736	\N	\N	\N	\N
ce5ea821-10eb-4c4b-9c48-809748f7656d	sales_ratio_study	TEST_COUNTY_A_244c1b	PENDING	\N	{"year": 2025}	2025-05-09 22:06:24.886229	2025-05-09 22:06:24.886232	\N	\N	\N	\N
0377066e-fdb3-45e8-b4da-ca33ebcc0269	assessment_roll	TEST_COUNTY_B_56faad	PENDING	\N	{"year": 2025}	2025-05-09 22:06:25.106433	2025-05-09 22:06:25.106436	\N	\N	\N	\N
24d0ba94-bed8-4b3b-947e-f3087abf7d8e	sales_ratio_study	TEST_COUNTY_B_7a51e8	PENDING	\N	{"year": 2025}	2025-05-09 22:06:25.298436	2025-05-09 22:06:25.298438	\N	\N	\N	\N
7d85b913-4699-4ac3-8ca5-c41a555cc975	assessment_roll	TEST_COUNTY_a24bf7af	COMPLETED	Report generated successfully	{"year": 2025}	2025-05-09 22:06:28.174915	2025-05-09 22:06:28.530404	2025-05-09 22:06:28.466526	2025-05-09 22:06:28.530407	s3://terrafusion-reports/TEST_COUNTY_a24bf7af/assessment_roll/7d85b913-4699-4ac3-8ca5-c41a555cc975.pdf	{"file_size_kb": 1024, "pages": 42, "generation_time_seconds": 3.5, "generated_at": "2025-05-09T22:06:28.528644"}
3d12f1d2-665d-4e2f-af6c-83ab56bb75db	assessment_roll	TEST_COUNTY_71bed438	PENDING	\N	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 22:06:37.40192	2025-05-09 22:06:37.401922	\N	\N	\N	\N
287c1d8a-1679-415e-9ebd-14e12ec57216	assessment_roll	TEST_COUNTY_A_eb875b	PENDING	\N	{"year": 2025}	2025-05-09 22:06:38.922192	2025-05-09 22:06:38.922196	\N	\N	\N	\N
a9a75806-0a24-4c1e-a9a5-607141b39989	sales_ratio_study	TEST_COUNTY_A_274673	PENDING	\N	{"year": 2025}	2025-05-09 22:06:39.13339	2025-05-09 22:06:39.133393	\N	\N	\N	\N
dfcbeef1-46ab-4fe4-8a47-c5967f49a687	assessment_roll	TEST_COUNTY_B_855350	PENDING	\N	{"year": 2025}	2025-05-09 22:06:39.344671	2025-05-09 22:06:39.344673	\N	\N	\N	\N
a425f317-ae5b-4ff6-8efb-bc754b09d568	sales_ratio_study	TEST_COUNTY_B_e0c579	PENDING	\N	{"year": 2025}	2025-05-09 22:06:39.589402	2025-05-09 22:06:39.589404	\N	\N	\N	\N
4ca01111-335d-42c7-856e-37e76202a7ce	assessment_roll	TEST_COUNTY_00d1f586	COMPLETED	Report generated successfully	{"year": 2025}	2025-05-09 22:06:42.586965	2025-05-09 22:06:42.985271	2025-05-09 22:06:42.920676	2025-05-09 22:06:42.985274	s3://terrafusion-reports/TEST_COUNTY_00d1f586/assessment_roll/4ca01111-335d-42c7-856e-37e76202a7ce.pdf	{"file_size_kb": 1024, "pages": 42, "generation_time_seconds": 3.5, "generated_at": "2025-05-09T22:06:42.981602"}
fcf27075-0977-4bfc-b567-7c81aeca0e19	assessment_roll	TEST_COUNTY_297bd0c7	PENDING	\N	{"year": 2025, "quarter": 2, "include_exempt": true}	2025-05-09 22:06:50.694882	2025-05-09 22:06:50.694885	\N	\N	\N	\N
5434bd95-038b-4072-8029-4faf8beb1220	assessment_roll	TEST_COUNTY_A_2a6bea	PENDING	\N	{"year": 2025}	2025-05-09 22:06:52.129027	2025-05-09 22:06:52.12903	\N	\N	\N	\N
63702b9a-7b2e-4c45-9a5a-86b525f8ec81	sales_ratio_study	TEST_COUNTY_A_2caac3	PENDING	\N	{"year": 2025}	2025-05-09 22:06:52.356601	2025-05-09 22:06:52.356603	\N	\N	\N	\N
50e4d8be-af65-456d-a7d3-905cdb7cd64b	assessment_roll	TEST_COUNTY_B_55d866	PENDING	\N	{"year": 2025}	2025-05-09 22:06:52.582094	2025-05-09 22:06:52.582096	\N	\N	\N	\N
6f6d41ad-4092-4405-9316-c4774c05e519	sales_ratio_study	TEST_COUNTY_B_6d582d	PENDING	\N	{"year": 2025}	2025-05-09 22:06:52.816653	2025-05-09 22:06:52.816655	\N	\N	\N	\N
5c18ce2a-1897-4452-a0b5-d7efa2585295
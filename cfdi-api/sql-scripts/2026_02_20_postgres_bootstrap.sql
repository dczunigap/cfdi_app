-- PostgreSQL bootstrap for production deployment (Hostinger VPS).
-- Run as postgres superuser:
--   psql -v ON_ERROR_STOP=1 -U postgres -f 2026_02_20_postgres_bootstrap.sql

-- 1) App role
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cfdi_user') THEN
        CREATE ROLE cfdi_user LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
    END IF;
END
$$;

ALTER ROLE cfdi_user WITH LOGIN;

-- 2) App database (psql \gexec required for IF NOT EXISTS behavior)
SELECT 'CREATE DATABASE cfdi_prod OWNER cfdi_user ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'cfdi_prod')\gexec

-- 3) DB-level hardening and grants
REVOKE ALL ON DATABASE cfdi_prod FROM PUBLIC;
GRANT CONNECT, TEMP ON DATABASE cfdi_prod TO cfdi_user;

\connect cfdi_prod

-- 4) Useful extension for UUID/random helpers
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 5) Schema-level grants (public schema is where SQLAlchemy creates tables by default)
GRANT USAGE, CREATE ON SCHEMA public TO cfdi_user;
ALTER SCHEMA public OWNER TO cfdi_user;

-- 6) Default privileges for future objects created by cfdi_user
ALTER DEFAULT PRIVILEGES FOR ROLE cfdi_user IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cfdi_user;

ALTER DEFAULT PRIVILEGES FOR ROLE cfdi_user IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO cfdi_user;


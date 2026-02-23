-- Reapply ownership/permissions on cfdi_prod.
-- Run as postgres superuser:
--   psql -v ON_ERROR_STOP=1 -U postgres -f 2026_02_20_postgres_app_user_perms.sql

\connect cfdi_prod

-- Ensure ownership for existing tables/sequences/functions under public schema.
DO $$
DECLARE
    r record;
BEGIN
    FOR r IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE public.%I OWNER TO cfdi_user', r.tablename);
    END LOOP;

    FOR r IN
        SELECT sequencename
        FROM pg_sequences
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER SEQUENCE public.%I OWNER TO cfdi_user', r.sequencename);
    END LOOP;
END
$$;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO cfdi_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cfdi_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO cfdi_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO cfdi_user;

ALTER DEFAULT PRIVILEGES FOR ROLE cfdi_user IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cfdi_user;

ALTER DEFAULT PRIVILEGES FOR ROLE cfdi_user IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO cfdi_user;

ALTER DEFAULT PRIVILEGES FOR ROLE cfdi_user IN SCHEMA public
GRANT EXECUTE ON FUNCTIONS TO cfdi_user;


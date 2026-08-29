#!/bin/bash
# Local Supabase initialization (local dev only).
# Authenticator password is taken from POSTGRES_PASSWORD (docker-compose default: postgres).

set -euo pipefail

AUTH_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
-- Create Supabase system roles
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'supabase_admin') THEN
        CREATE ROLE supabase_admin NOLOGIN NOINHERIT BYPASSRLS;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticator') THEN
        EXECUTE format('CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD %L', '${AUTH_PASSWORD}');
    END IF;
END
\$\$;

GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON SCHEMA public TO supabase_admin;

CREATE SCHEMA IF NOT EXISTS auth;

CREATE OR REPLACE FUNCTION auth.role()
RETURNS TEXT AS \$\$
BEGIN
    RETURN COALESCE(
        current_setting('request.jwt.claim.role', true),
        current_setting('request.jwt.claims', true)::json->>'role',
        'anon'
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'anon';
END;
\$\$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION auth.uid()
RETURNS UUID AS \$\$
BEGIN
    RETURN COALESCE(
        (current_setting('request.jwt.claims', true)::json->>'sub')::uuid,
        NULL
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
\$\$ LANGUAGE plpgsql STABLE;

GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.role() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.uid() TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO authenticated;
EOSQL

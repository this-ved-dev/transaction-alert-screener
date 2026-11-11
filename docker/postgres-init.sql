-- Runs once on first start. The app connects as screener_app, which can read and write
-- everything except that it can never UPDATE or DELETE audit rows (C9: append-only evidence).
-- Table grants are applied by the Django migration in TRA-11 after the audit_log table exists;
-- this file only creates the role and the default privileges.
\set app_pw `echo "$POSTGRES_APP_PASSWORD"`
CREATE ROLE screener_app LOGIN PASSWORD :'app_pw';
GRANT CONNECT ON DATABASE screener TO screener_app;
GRANT USAGE, CREATE ON SCHEMA public TO screener_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO screener_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO screener_app;
-- TRA-11 adds, inside the migration that creates audit_log:
--   REVOKE UPDATE, DELETE ON audit_log FROM screener_app;

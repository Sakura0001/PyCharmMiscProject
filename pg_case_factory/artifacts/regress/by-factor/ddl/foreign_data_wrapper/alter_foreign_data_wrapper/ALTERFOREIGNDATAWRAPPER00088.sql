-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER FOREIGN DATA WRAPPER conditional product: actor=superuser, branch=owner, expected_sqlstate=42704, fdw_name_shape=nonexistent_name, object_state=missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNDATAWRAPPER00088
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_data_wrapper/alter_foreign_data_wrapper.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_data_wrapper/alter_foreign_data_wrapper.yaml
-- factor_values: statement_branch=branch_owner, object_state=not_exists, expected_status=failure, alter_action=owner, fdw_name_shape=nonexistent_name, privilege_level=superuser, nonexistent_fdw=fdw_missing, non_superuser_attempt=superuser_execution, verification_mode=error_assertion, cleanup_mode=revert_owner
-- derived_axes: actor=superuser, branch=owner, expected_sqlstate=42704, fdw_name_shape=nonexistent_name, object_state=missing
-- combination_strategy: full PostgreSQL 18 branch-applicable conditional products; no sampling
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42704; pg_foreign_data_wrapper catalog/effect oracle

-- 1. Header and immutable trace metadata are complete above.

-- 2. Session settings are explicit and reset during cleanup.

-- 3. Idempotent pre-cleanup.
RESET ROLE;
RESET search_path;
DROP SERVER IF EXISTS alterforeigndatawrapper_00088_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigndatawrapper_00088_missing_fdw CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigndatawrapper_00088_renamed_fdw CASCADE;
DROP EXTENSION IF EXISTS postgres_fdw CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_handler() CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_handler(integer) CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_validator(text[], oid) CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_validator(text[]) CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_valid_validator(text[], oid) CASCADE;
DROP ROLE IF EXISTS alterforeigndatawrapper_00088_intruder;
DROP ROLE IF EXISTS alterforeigndatawrapper_00088_new_owner;
DROP ROLE IF EXISTS "FDW Quoted Owner 00088";

-- 4. FDW, role, support-function, server, and foreign-table fixture.
CREATE EXTENSION postgres_fdw;
CREATE ROLE alterforeigndatawrapper_00088_new_owner SUPERUSER;
CREATE ROLE "FDW Quoted Owner 00088" SUPERUSER;
CREATE ROLE alterforeigndatawrapper_00088_intruder;
SET search_path TO public, pg_catalog;
CREATE FUNCTION public.alterforeigndatawrapper_00088_valid_validator(text[], oid) RETURNS void LANGUAGE plpgsql AS $body$ DECLARE item text; BEGIN FOREACH item IN ARRAY $1 LOOP IF pg_catalog.split_part(item, '=', 1) = 'invalid_option' OR pg_catalog.split_part(item, '=', 1) LIKE 'legacy%' THEN RAISE EXCEPTION 'invalid option %', pg_catalog.split_part(item, '=', 1) USING ERRCODE='HV00D'; END IF; END LOOP; END $body$;

-- 5. Fixture is complete and each failure has one primary cause.
SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;

-- 6. Capture FDW identity, owner, handler, validator, and options.
SELECT
    COALESCE((SELECT oid::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname='alterforeigndatawrapper_00088_missing_fdw'), '0') AS before_fdw_oid,
    COALESCE((SELECT fdwowner::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname='alterforeigndatawrapper_00088_missing_fdw'), '0') AS before_fdw_owner,
    COALESCE((SELECT fdwhandler::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname='alterforeigndatawrapper_00088_missing_fdw'), '0') AS before_fdw_handler,
    COALESCE((SELECT fdwvalidator::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname='alterforeigndatawrapper_00088_missing_fdw'), '0') AS before_fdw_validator,
    COALESCE((SELECT pg_catalog.array_to_string(fdwoptions, E'\n') FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname='alterforeigndatawrapper_00088_missing_fdw'), '<NULL>') AS before_fdw_options
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY before_fdw_oid;
\gset

-- 7. Select the declared executor.

-- 8. Primary target statement (exactly one coverage-credit operation).
\set ON_ERROR_STOP off
ALTER FOREIGN DATA WRAPPER alterforeigndatawrapper_00088_missing_fdw OWNER TO alterforeigndatawrapper_00088_new_owner;
\set alter_fdw_sqlstate :SQLSTATE
\set ON_ERROR_STOP on

-- 9. SQLSTATE and primary-result oracle.
SELECT :'alter_fdw_sqlstate' = '42704' AS expected_SQLSTATE;
RESET ROLE;

-- 10. Catalog, dependency, and downstream-effect verification.
SELECT COALESCE(pg_catalog.bool_and(
    fdwowner::text = :'before_fdw_owner'
    AND fdwhandler::text = :'before_fdw_handler'
    AND fdwvalidator::text = :'before_fdw_validator'
    AND COALESCE(pg_catalog.array_to_string(fdwoptions, E'\n'), '<NULL>') = :'before_fdw_options'
), :'before_fdw_oid' = '0') AS failed_or_rolled_back_fdw_unchanged
FROM pg_catalog.pg_foreign_data_wrapper
WHERE :'before_fdw_oid' <> '0' AND oid=:'before_fdw_oid'::oid
ORDER BY failed_or_rolled_back_fdw_unchanged;

-- 11. Remove foreign tables, servers, wrappers, functions, and roles.
RESET ROLE;
RESET search_path;
DROP SERVER IF EXISTS alterforeigndatawrapper_00088_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigndatawrapper_00088_missing_fdw CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigndatawrapper_00088_renamed_fdw CASCADE;
DROP EXTENSION IF EXISTS postgres_fdw CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_handler() CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_handler(integer) CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_validator(text[], oid) CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_validator(text[]) CASCADE;
DROP FUNCTION IF EXISTS public.alterforeigndatawrapper_00088_valid_validator(text[], oid) CASCADE;
DROP ROLE IF EXISTS alterforeigndatawrapper_00088_intruder;
DROP ROLE IF EXISTS alterforeigndatawrapper_00088_new_owner;
DROP ROLE IF EXISTS "FDW Quoted Owner 00088";
SELECT
    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_foreign_data_wrapper
                WHERE fdwname IN ('alterforeigndatawrapper_00088_missing_fdw', 'alterforeigndatawrapper_00088_renamed_fdw'))
    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles
                    WHERE rolname IN ('alterforeigndatawrapper_00088_new_owner', 'FDW Quoted Owner 00088', 'alterforeigndatawrapper_00088_intruder')) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;

-- 12. Cleanup oracle is the final deterministic verification above.

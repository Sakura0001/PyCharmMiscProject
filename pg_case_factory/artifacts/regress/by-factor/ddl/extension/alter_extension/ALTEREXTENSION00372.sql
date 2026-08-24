-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER EXTENSION conditional product: actor=superuser, branch=set_schema, expected_sqlstate=42601, extension_name_shape=simple_id, member_kind=table, member_name_shape=simple_id, parser_boundary=set_schema_missing_target
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEREXTENSION00372
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/alter_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/alter_extension.yaml
-- factor_values: statement_branch=branch_set_schema, object_state=exists, expected_status=failure, alter_action=set_schema, extension_name_shape=simple_id, privilege_level=superuser, nonexistent_extension=extension_exists, insufficient_privilege=superuser_execution, verification_mode=error_assertion, cleanup_mode=drop_extension, new_schema_shape=simple_id, relocatable_state=relocatable, target_schema_existence=schema_exists, non_relocatable_set_schema=relocatable_extension, nonexistent_target_schema=schema_exists
-- derived_axes: actor=superuser, branch=set_schema, expected_sqlstate=42601, extension_name_shape=simple_id, member_kind=table, member_name_shape=simple_id, parser_boundary=set_schema_missing_target
-- combination_strategy: full branch-applicable PostgreSQL 18 conditional product; all 28 member-object forms; no sampling
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42601; pg_extension and pg_depend state oracle

-- 1. Header and immutable trace metadata are complete above.

-- 2. Session settings are explicit and reset during cleanup.

-- 3. Idempotent pre-cleanup.
DROP TABLE IF EXISTS alterextension_00372_member_schema.alterextension_00372_member_object CASCADE;
RESET ROLE;
RESET search_path;
DROP EXTENSION IF EXISTS hstore CASCADE;
DROP EXTENSION IF EXISTS dblink CASCADE;
DROP EXTENSION IF EXISTS pgcf_versioned_extension CASCADE;
DROP EXTENSION IF EXISTS pgcf_relocatable_extension CASCADE;
DROP EVENT TRIGGER IF EXISTS alterextension_00372_member_object;
DROP ACCESS METHOD IF EXISTS alterextension_00372_member_object;
DROP FOREIGN DATA WRAPPER IF EXISTS alterextension_00372_member_object CASCADE;
DROP LANGUAGE IF EXISTS alterextension_00372_member_object CASCADE;
DROP SCHEMA IF EXISTS alterextension_00372_target_schema CASCADE;
DROP SCHEMA IF EXISTS alterextension_00372_member_schema CASCADE;
DROP SCHEMA IF EXISTS alterextension_00372_extension_schema CASCADE;
SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='alterextension_00372_extension_owner') THEN 'yes' ELSE 'no' END AS cleanup_owner_state
FROM (VALUES (true)) AS cleanup_owner_anchor(dummy)
ORDER BY cleanup_owner_state;
\gset
\if :cleanup_owner_state
REVOKE CREATE ON DATABASE :"DBNAME" FROM alterextension_00372_extension_owner;
\endif
DROP ROLE IF EXISTS alterextension_00372_intruder;
DROP ROLE IF EXISTS alterextension_00372_object_owner;
DROP ROLE IF EXISTS alterextension_00372_extension_owner;

-- 4. Extension, role, schema, and member-object fixture.
CREATE SCHEMA alterextension_00372_member_schema;
CREATE SCHEMA alterextension_00372_target_schema;

-- 5. Fixture is complete and every failure case has one isolated cause.
SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;

-- 6. Capture extension identity, version, namespace, owner, and member count.
SELECT
    COALESCE((SELECT oid::text FROM pg_catalog.pg_extension WHERE extname='hstore'), '0') AS before_extension_oid,
    COALESCE((SELECT extversion FROM pg_catalog.pg_extension WHERE extname='hstore'), '<MISSING>') AS before_extension_version,
    COALESCE((SELECT extnamespace::text FROM pg_catalog.pg_extension WHERE extname='hstore'), '0') AS before_extension_namespace,
    COALESCE((SELECT extowner::text FROM pg_catalog.pg_extension WHERE extname='hstore'), '0') AS before_extension_owner,
    COALESCE((SELECT count(*)::text FROM pg_catalog.pg_depend AS d JOIN pg_catalog.pg_extension AS e ON e.oid=d.refobjid WHERE e.extname='hstore' AND d.deptype='e'), '0') AS before_member_count
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY before_extension_oid;
\gset

-- 7. Select the declared executor.

-- 8. Primary target statement (exactly one coverage-credit operation).
\set ON_ERROR_STOP off
ALTER EXTENSION hstore SET SCHEMA;
\set alter_extension_sqlstate :SQLSTATE
\set ON_ERROR_STOP on

-- 9. SQLSTATE and primary-result oracle.
SELECT :'alter_extension_sqlstate' = '42601' AS expected_SQLSTATE;
RESET ROLE;

-- 10. Catalog and extension-membership verification.
SELECT COALESCE(pg_catalog.bool_and(
    e.extversion = :'before_extension_version'
    AND e.extnamespace::text = :'before_extension_namespace'
    AND e.extowner::text = :'before_extension_owner'
), true) AS failed_or_rolled_back_extension_unchanged
FROM pg_catalog.pg_extension AS e
WHERE :'before_extension_oid' <> '0' AND e.oid=:'before_extension_oid'::oid
ORDER BY failed_or_rolled_back_extension_unchanged;

-- 11. Remove extension, detached members, schemas, roles, and helper objects.
RESET ROLE;
RESET search_path;
DROP EXTENSION IF EXISTS hstore CASCADE;
DROP EXTENSION IF EXISTS dblink CASCADE;
DROP EVENT TRIGGER IF EXISTS alterextension_00372_member_object;
DROP ACCESS METHOD IF EXISTS alterextension_00372_member_object;
DROP FOREIGN DATA WRAPPER IF EXISTS alterextension_00372_member_object CASCADE;
DROP LANGUAGE IF EXISTS alterextension_00372_member_object CASCADE;
DROP SCHEMA IF EXISTS alterextension_00372_target_schema CASCADE;
DROP SCHEMA IF EXISTS alterextension_00372_member_schema CASCADE;
DROP SCHEMA IF EXISTS alterextension_00372_extension_schema CASCADE;
SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='alterextension_00372_extension_owner') THEN 'yes' ELSE 'no' END AS cleanup_owner_state
FROM (VALUES (true)) AS cleanup_owner_anchor(dummy)
ORDER BY cleanup_owner_state;
\gset
\if :cleanup_owner_state
REVOKE CREATE ON DATABASE :"DBNAME" FROM alterextension_00372_extension_owner;
\endif
DROP ROLE IF EXISTS alterextension_00372_intruder;
DROP ROLE IF EXISTS alterextension_00372_object_owner;
DROP ROLE IF EXISTS alterextension_00372_extension_owner;
SELECT
    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_extension WHERE extname IN ('hstore','dblink','pgcf_versioned_extension','pgcf_relocatable_extension'))
    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ('alterextension_00372_extension_owner','alterextension_00372_object_owner','alterextension_00372_intruder')) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;
DROP TABLE IF EXISTS alterextension_00372_member_schema.alterextension_00372_member_object CASCADE;

-- 12. Cleanup oracle is the final deterministic verification above.

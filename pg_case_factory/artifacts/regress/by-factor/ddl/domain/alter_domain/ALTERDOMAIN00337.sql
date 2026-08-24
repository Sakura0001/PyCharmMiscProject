-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER DOMAIN conditional product: actor=superuser, base_sample=1, base_type=INTEGER, branch=set_default, concurrent_hazard=safe_serial_execution, container_block=no_container_block, container_usage=not_used_in_container, domain_name_shape=schema_qualified, expected_sqlstate=00000, ordinal_text=00337, type_declaration=pgcf_mood, type_form=set_default, type_key=enum_type, type_sample='ok'
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERDOMAIN00337
-- source_md: skills/pg-sql-generation/references/statements/ddl/domain/alter_domain.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/domain/alter_domain.yaml
-- factor_values: statement_branch=branch_set_default, object_state=exists, expected_status=success, alter_action=set_default, domain_name_shape=schema_qualified, privilege_level=superuser, nonexistent_domain=domain_exists, non_owner_attempt=superuser_execution, container_column_usage=not_used_in_container, container_column_block=no_container_block, null_value_block=no_null_values, concurrent_data_hazard=safe_serial_execution, verification_mode=catalog_query_pg_type, cleanup_mode=revert_alter
-- derived_axes: actor=superuser, base_sample=1, base_type=INTEGER, branch=set_default, concurrent_hazard=safe_serial_execution, container_block=no_container_block, container_usage=not_used_in_container, domain_name_shape=schema_qualified, expected_sqlstate=00000, ordinal_text=00337, type_declaration=pgcf_mood, type_form=set_default, type_key=enum_type, type_sample='ok', type_setup_json=["CREATE TYPE pgcf_mood AS ENUM ('sad', 'ok', 'happy');"]
-- combination_strategy: full applicable conditional product; outcome and aliases are resolver-derived
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000; pg_type/pg_constraint/effect and cleanup oracles

-- 1. Header and immutable trace metadata are complete above.

-- 2. Session profile follows the frozen single/external route.

-- 3. Idempotent pre-cleanup.
DROP TABLE IF EXISTS alterdomain_00337_source_schema.alterdomain_00337_holder_table CASCADE;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS alterdomain_00337_target_schema CASCADE;
DROP SCHEMA IF EXISTS alterdomain_00337_source_schema CASCADE;
DROP ROLE IF EXISTS alterdomain_00337_intruder;
DROP ROLE IF EXISTS alterdomain_00337_new_owner;
DROP ROLE IF EXISTS alterdomain_00337_domain_owner;

-- 4. Roles, schemas, domain base type, complete table, and container fixtures.
SET client_min_messages TO warning;
CREATE ROLE alterdomain_00337_domain_owner;
CREATE ROLE alterdomain_00337_intruder;
CREATE ROLE alterdomain_00337_new_owner;
CREATE SCHEMA alterdomain_00337_source_schema;
GRANT USAGE, CREATE ON SCHEMA alterdomain_00337_source_schema TO alterdomain_00337_domain_owner;
GRANT USAGE ON SCHEMA alterdomain_00337_source_schema TO alterdomain_00337_intruder;
CREATE SCHEMA alterdomain_00337_target_schema;
SET search_path TO alterdomain_00337_source_schema, pg_catalog;
CREATE TYPE alterdomain_00337_type_mood AS ENUM ('sad', 'ok', 'happy');
SET ROLE alterdomain_00337_domain_owner;
CREATE DOMAIN alterdomain_00337_source_schema.alterdomain_00337_domain_value AS alterdomain_00337_type_mood;
RESET ROLE;
CREATE TABLE alterdomain_00337_source_schema.alterdomain_00337_holder_table (
    id bigint NOT NULL,
    tenant_id bigint NOT NULL,
    domain_value alterdomain_00337_source_schema.alterdomain_00337_domain_value,
    payload text NOT NULL,
    amount numeric(18,2) NOT NULL CHECK (amount >= 0),
    status smallint NOT NULL DEFAULT 0 CHECK (status BETWEEN 0 AND 9),
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT alterdomain_00337_holder_pk PRIMARY KEY (id),
    CONSTRAINT alterdomain_00337_holder_uk UNIQUE (tenant_id, id)
);
INSERT INTO alterdomain_00337_source_schema.alterdomain_00337_holder_table(id, tenant_id, domain_value, payload, amount, status) VALUES (1, 10, 'ok', 'alpha', 12.50, 1);

-- 5. Fixtures isolate exactly one intended semantic or failure condition.
SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;

-- 6. Capture stable pg_type state before the target.
SELECT
    COALESCE((SELECT t.oid::text FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace
              WHERE ns.nspname='alterdomain_00337_source_schema' AND t.typname='alterdomain_00337_domain_value' AND t.typtype='d'), '0') AS before_domain_oid,
    COALESCE((SELECT t.typname FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace
              WHERE ns.nspname='alterdomain_00337_source_schema' AND t.typname='alterdomain_00337_domain_value' AND t.typtype='d'), '<MISSING>') AS before_domain_name,
    COALESCE((SELECT t.typnotnull::text FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace
              WHERE ns.nspname='alterdomain_00337_source_schema' AND t.typname='alterdomain_00337_domain_value' AND t.typtype='d'), '<MISSING>') AS before_domain_notnull,
    COALESCE((SELECT COALESCE(t.typdefault, '<NULL>') FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace
              WHERE ns.nspname='alterdomain_00337_source_schema' AND t.typname='alterdomain_00337_domain_value' AND t.typtype='d'), '<MISSING>') AS before_domain_default
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY before_domain_oid;
\gset

-- 7. Select the authorized or deliberately unauthorized executor.

-- 8. Primary target statement (exactly one coverage-credit operation).
\set ON_ERROR_STOP off
ALTER DOMAIN alterdomain_00337_source_schema.alterdomain_00337_domain_value SET DEFAULT 'ok';
\set alter_domain_sqlstate :SQLSTATE
\set ON_ERROR_STOP on

-- 9. SQLSTATE and primary-result oracle.
SELECT :'alter_domain_sqlstate' = '00000' AS expected_SQLSTATE;
RESET ROLE;

-- 10. Catalog, constraint, data-effect, and concurrency verification.
SELECT
    CASE WHEN :'before_domain_oid' = '0' THEN true ELSE EXISTS (
        SELECT 1 FROM pg_catalog.pg_type AS t
        WHERE t.oid = :'before_domain_oid'::oid AND t.typtype = 'd'
    ) END AS domain_identity_preserved
FROM (VALUES (true)) AS identity_anchor(dummy)
ORDER BY domain_identity_preserved;
SELECT t.typdefault IS NOT NULL AS domain_default_set FROM pg_catalog.pg_type AS t WHERE t.oid=:'before_domain_oid'::oid ORDER BY domain_default_set;

-- 11. Remove dependent tables, domains, schemas, and roles.
RESET ROLE;
DROP SCHEMA IF EXISTS alterdomain_00337_target_schema CASCADE;
DROP SCHEMA IF EXISTS alterdomain_00337_source_schema CASCADE;
DROP ROLE IF EXISTS alterdomain_00337_intruder;
DROP ROLE IF EXISTS alterdomain_00337_new_owner;
DROP ROLE IF EXISTS alterdomain_00337_domain_owner;
SELECT
    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname IN ('alterdomain_00337_source_schema', 'alterdomain_00337_target_schema'))
    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ('alterdomain_00337_domain_owner', 'alterdomain_00337_new_owner', 'alterdomain_00337_intruder')) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;

-- 12. Cleanup oracle is the final executable query above.
DROP TABLE IF EXISTS alterdomain_00337_source_schema.alterdomain_00337_holder_table CASCADE;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER EVENT TRIGGER conditional product: actor=superuser, branch=disable, current_state=enabled, expected_sqlstate=42704, function_state=function_not_exists, object_state=not_exists, session_role=origin, trigger_name_shape=nonexistent_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEREVENTTRIGGER00141
-- source_md: skills/pg-sql-generation/references/statements/ddl/event_trigger/alter_event_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/event_trigger/alter_event_trigger.yaml
-- factor_values: statement_branch=branch_disable, object_state=not_exists, expected_status=failure, privilege_level=superuser, trigger_current_state=enabled, trigger_name_shape=nonexistent_name, session_replication_role=origin, trigger_function_state=function_not_exists, trigger_not_exist=trigger_not_exists, privilege_denied_non_superuser=superuser_success, alter_nonexistent_trigger=trigger_not_exists, verification_mode=error_assertion, cleanup_mode=cascade_cleanup
-- derived_axes: actor=superuser, branch=disable, current_state=enabled, expected_sqlstate=42704, function_state=function_not_exists, object_state=not_exists, session_role=origin, trigger_name_shape=nonexistent_name
-- combination_strategy: full branch-applicable conditional product; no table/type axes
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42704; pg_event_trigger state/owner/name and firing oracle

-- 1. Header and immutable trace metadata are complete above.

-- 2. Session settings are explicit and reset during cleanup.

-- 3. Idempotent pre-cleanup.
RESET ROLE;
SET session_replication_role TO origin;
DROP SCHEMA IF EXISTS altereventtrigger_00141_probe_schema CASCADE;
DROP EVENT TRIGGER IF EXISTS altereventtrigger_00141_event_trigger;
DROP EVENT TRIGGER IF EXISTS altereventtrigger_00141_new_trigger;
DROP EVENT TRIGGER IF EXISTS altereventtrigger_00141_conflict_trigger;
DROP FUNCTION IF EXISTS public.altereventtrigger_00141_event_function() CASCADE;
DROP ROLE IF EXISTS altereventtrigger_00141_new_owner;
DROP ROLE IF EXISTS altereventtrigger_00141_intruder;
SELECT
    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_event_trigger WHERE evtname IN ('altereventtrigger_00141_event_trigger', 'altereventtrigger_00141_new_trigger', 'altereventtrigger_00141_conflict_trigger'))
    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc WHERE proname='altereventtrigger_00141_event_function')
    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ('altereventtrigger_00141_new_owner', 'altereventtrigger_00141_intruder')) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;

-- 4. Event-trigger function, roles, and trigger fixture.
SET client_min_messages TO warning;
SET session_replication_role TO origin;
CREATE ROLE altereventtrigger_00141_intruder;
CREATE ROLE altereventtrigger_00141_new_owner;
CREATE FUNCTION public.altereventtrigger_00141_event_function() RETURNS event_trigger
LANGUAGE plpgsql
AS $body$ BEGIN PERFORM pg_catalog.set_config('pgcf.altereventtrigger_00141_fired', '1', false); END $body$;
DROP FUNCTION public.altereventtrigger_00141_event_function() CASCADE;

-- 5. Function and target existence states are isolated above.
SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;

-- 6. Capture the exact pg_event_trigger state.
SELECT
    COALESCE((SELECT oid::text FROM pg_catalog.pg_event_trigger WHERE evtname='altereventtrigger_00141_event_trigger'), '0') AS before_trigger_oid,
    COALESCE((SELECT evtenabled::text FROM pg_catalog.pg_event_trigger WHERE evtname='altereventtrigger_00141_event_trigger'), '<MISSING>') AS before_trigger_state,
    COALESCE((SELECT evtname FROM pg_catalog.pg_event_trigger WHERE evtname='altereventtrigger_00141_event_trigger'), '<MISSING>') AS before_trigger_name,
    COALESCE((SELECT evtowner::text FROM pg_catalog.pg_event_trigger WHERE evtname='altereventtrigger_00141_event_trigger'), '<MISSING>') AS before_trigger_owner
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY before_trigger_oid;
\gset

-- 7. Select the superuser or deliberate non-superuser executor.

-- 8. Primary target statement (exactly one coverage-credit operation).
\set ON_ERROR_STOP off
ALTER EVENT TRIGGER altereventtrigger_00141_missing_trigger DISABLE;
\set alter_event_trigger_sqlstate :SQLSTATE
\set ON_ERROR_STOP on

-- 9. SQLSTATE and primary-result oracle.
SELECT :'alter_event_trigger_sqlstate' = '42704' AS expected_SQLSTATE;
RESET ROLE;

-- 10. Catalog and actual firing-semantics verification.
SELECT COALESCE(pg_catalog.bool_and(
    e.evtenabled::text = :'before_trigger_state'
    AND e.evtname = :'before_trigger_name'
    AND e.evtowner::text = :'before_trigger_owner'
), true) AS failed_or_rolled_back_state_unchanged
FROM pg_catalog.pg_event_trigger AS e
WHERE :'before_trigger_oid' <> '0' AND e.oid=:'before_trigger_oid'::oid
ORDER BY failed_or_rolled_back_state_unchanged;

-- 11. Drop trigger, function, probe schema, and roles.
RESET ROLE;
SET session_replication_role TO origin;
DROP SCHEMA IF EXISTS altereventtrigger_00141_probe_schema CASCADE;
DROP EVENT TRIGGER IF EXISTS altereventtrigger_00141_event_trigger;
DROP EVENT TRIGGER IF EXISTS altereventtrigger_00141_new_trigger;
DROP EVENT TRIGGER IF EXISTS altereventtrigger_00141_conflict_trigger;
DROP FUNCTION IF EXISTS public.altereventtrigger_00141_event_function() CASCADE;
DROP ROLE IF EXISTS altereventtrigger_00141_new_owner;
DROP ROLE IF EXISTS altereventtrigger_00141_intruder;
SELECT
    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_event_trigger WHERE evtname IN ('altereventtrigger_00141_event_trigger', 'altereventtrigger_00141_new_trigger', 'altereventtrigger_00141_conflict_trigger'))
    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc WHERE proname='altereventtrigger_00141_event_function')
    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ('altereventtrigger_00141_new_owner', 'altereventtrigger_00141_intruder')) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;

-- 12. Cleanup oracle is the final executable query above.

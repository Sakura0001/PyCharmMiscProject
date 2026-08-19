-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR branch_owner=bounded_cross_branch_owner_catalog_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR00125
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-EXT|00125|owner_change|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_00125_sch;
CREATE TYPE alteroperator_00125_custom_type AS (val integer);
CREATE SCHEMA IF NOT EXISTS alteroperator_00125_target_sch;
CREATE FUNCTION alteroperator_00125_sch.alteroperator_00125_op_proc(l alteroperator_00125_custom_type, r alteroperator_00125_custom_type) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE ROLE alteroperator_00125_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperator_00125_sch TO alteroperator_00125_actor;
CREATE OPERATOR alteroperator_00125_sch.#~ ( PROCEDURE = alteroperator_00125_sch.alteroperator_00125_op_proc, LEFTARG = alteroperator_00125_custom_type, RIGHTARG = alteroperator_00125_custom_type );
SET ROLE alteroperator_00125_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR alteroperator_00125_sch.#~ (alteroperator_00125_custom_type, alteroperator_00125_custom_type) OWNER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS op_owner_changed FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'alteroperator_00125_custom_type'::regtype AND oprright = 'alteroperator_00125_custom_type'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_00125_sch') AND oprowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = current_role) ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperator_00125_sch CASCADE;
DROP TYPE IF EXISTS alteroperator_00125_custom_type CASCADE;
DROP SCHEMA IF EXISTS alteroperator_00125_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_00125_sch.alteroperator_00125_op_proc CASCADE;
DROP OWNED BY alteroperator_00125_actor;
DROP ROLE IF EXISTS alteroperator_00125_actor;

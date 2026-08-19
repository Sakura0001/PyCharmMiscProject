-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR branch_owner=bounded_cross_branch_owner_error_assertion_drop_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR00134
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-EXT|00134|owner_change|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_00134_sch;
CREATE TYPE alteroperator_00134_custom_type AS (val integer);
CREATE SCHEMA IF NOT EXISTS alteroperator_00134_target_sch;
CREATE FUNCTION alteroperator_00134_sch.alteroperator_00134_op_proc(l alteroperator_00134_custom_type, r alteroperator_00134_custom_type) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE ROLE alteroperator_00134_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperator_00134_sch TO alteroperator_00134_actor;
CREATE OPERATOR alteroperator_00134_sch.#~ ( PROCEDURE = alteroperator_00134_sch.alteroperator_00134_op_proc, LEFTARG = alteroperator_00134_custom_type, RIGHTARG = alteroperator_00134_custom_type );
SET ROLE alteroperator_00134_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR alteroperator_00134_sch.#~ (alteroperator_00134_custom_type, alteroperator_00134_custom_type) OWNER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS op_present FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'alteroperator_00134_custom_type'::regtype AND oprright = 'alteroperator_00134_custom_type'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_00134_sch') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperator_00134_sch CASCADE;
DROP TYPE IF EXISTS alteroperator_00134_custom_type CASCADE;
DROP SCHEMA IF EXISTS alteroperator_00134_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_00134_sch.alteroperator_00134_op_proc CASCADE;
DROP OWNED BY alteroperator_00134_actor;
DROP ROLE IF EXISTS alteroperator_00134_actor;

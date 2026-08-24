-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR ownership_boundary=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR00041
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-SFV|sfv-0fff29baf6583df42ef111ec|owner_change
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_00041_sch;
CREATE SCHEMA IF NOT EXISTS alteroperator_00041_target_sch;
CREATE FUNCTION alteroperator_00041_sch.alteroperator_00041_op_proc(l integer, r integer) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE ROLE alteroperator_00041_new_owner LOGIN;
CREATE ROLE alteroperator_00041_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperator_00041_sch TO alteroperator_00041_actor;
CREATE OPERATOR alteroperator_00041_sch.#~ ( PROCEDURE = alteroperator_00041_sch.alteroperator_00041_op_proc, LEFTARG = integer, RIGHTARG = integer );
SET ROLE alteroperator_00041_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR alteroperator_00041_sch.#~ (integer, integer) OWNER TO alteroperator_00041_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS op_owner_changed FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_00041_sch') AND oprowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alteroperator_00041_new_owner') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperator_00041_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_00041_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_00041_sch.alteroperator_00041_op_proc CASCADE;
DROP ROLE IF EXISTS alteroperator_00041_new_owner;
DROP OWNED BY alteroperator_00041_actor;
DROP ROLE IF EXISTS alteroperator_00041_actor;

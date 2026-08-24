-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR privilege_context=superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR00047
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-SFV|sfv-c459e226e0edbaddbd848205|owner_change
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperator_00047_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_00047_sch;
CREATE SCHEMA IF NOT EXISTS alteroperator_00047_target_sch;
CREATE FUNCTION alteroperator_00047_sch.alteroperator_00047_op_proc(l integer, r integer) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE ROLE alteroperator_00047_new_owner LOGIN;
CREATE OPERATOR alteroperator_00047_sch.#~ ( PROCEDURE = alteroperator_00047_sch.alteroperator_00047_op_proc, LEFTARG = integer, RIGHTARG = integer );
-- primary-target-begin
ALTER OPERATOR alteroperator_00047_sch.#~ (integer, integer) OWNER TO alteroperator_00047_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=00000
-- 4. 断言与目录审计。
SELECT count(*) AS op_owner_changed FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_00047_sch') AND oprowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alteroperator_00047_new_owner') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperator_00047_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_00047_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_00047_sch.alteroperator_00047_op_proc CASCADE;
DROP ROLE IF EXISTS alteroperator_00047_new_owner;

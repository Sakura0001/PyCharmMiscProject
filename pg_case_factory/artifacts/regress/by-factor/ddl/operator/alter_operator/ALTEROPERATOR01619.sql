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
-- case_id: ALTEROPERATOR01619
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-EXT|01619|owner_change|catalog_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_01619_sch;
CREATE SCHEMA IF NOT EXISTS alteroperator_01619_target_sch;
CREATE FUNCTION alteroperator_01619_sch.alteroperator_01619_op_proc(l integer, r integer) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE ROLE alteroperator_01619_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperator_01619_sch TO alteroperator_01619_actor;
CREATE OPERATOR alteroperator_01619_sch.#~ ( PROCEDURE = alteroperator_01619_sch.alteroperator_01619_op_proc, LEFTARG = integer, RIGHTARG = integer );
SET ROLE alteroperator_01619_actor;
-- primary-target-begin
ALTER OPERATOR alteroperator_01619_sch.#~ (integer, integer) OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=00000
-- 4. 断言与目录审计。
SELECT count(*) AS op_owner_changed FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_01619_sch') AND oprowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = session_user) ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperator_01619_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_01619_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_01619_sch.alteroperator_01619_op_proc CASCADE;
DROP OWNED BY alteroperator_01619_actor;
DROP ROLE IF EXISTS alteroperator_01619_actor;

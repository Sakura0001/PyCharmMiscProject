-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR branch_owner=bounded_cross_branch_owner_effect_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR01435
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-EXT|01435|owner_change|effect_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperator_01435_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_01435_sch;
CREATE SCHEMA IF NOT EXISTS alteroperator_01435_target_sch;
CREATE FUNCTION alteroperator_01435_sch.alteroperator_01435_op_proc(l text, r text) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE ROLE alteroperator_01435_new_owner LOGIN;
CREATE OPERATOR alteroperator_01435_sch.#~ ( PROCEDURE = alteroperator_01435_sch.alteroperator_01435_op_proc, LEFTARG = text, RIGHTARG = text );
-- primary-target-begin
ALTER OPERATOR alteroperator_01435_sch.#~ (text, text) OWNER TO alteroperator_01435_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=00000
-- 4. 断言与目录审计。
SELECT count(*) AS op_owner_changed FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'text'::regtype AND oprright = 'text'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_01435_sch') AND oprowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alteroperator_01435_new_owner') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperator_01435_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_01435_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_01435_sch.alteroperator_01435_op_proc CASCADE;
DROP ROLE IF EXISTS alteroperator_01435_new_owner;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR branch_set_estimator=bounded_cross_branch_set_estimator_effect_query_drop_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR02184
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-EXT|02184|set_estimator|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_02184_sch;
CREATE SCHEMA IF NOT EXISTS alteroperator_02184_target_sch;
CREATE FUNCTION alteroperator_02184_sch.alteroperator_02184_op_proc(l text, r text) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE ROLE alteroperator_02184_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperator_02184_sch TO alteroperator_02184_actor;
CREATE OPERATOR alteroperator_02184_sch.#~ ( PROCEDURE = alteroperator_02184_sch.alteroperator_02184_op_proc, LEFTARG = text, RIGHTARG = text );
SET ROLE alteroperator_02184_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR alteroperator_02184_sch.#~ (text, text) SET (RESTRICT = eqsel);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS op_present FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'text'::regtype AND oprright = 'text'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_02184_sch') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperator_02184_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_02184_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_02184_sch.alteroperator_02184_op_proc CASCADE;
DROP OWNED BY alteroperator_02184_actor;
DROP ROLE IF EXISTS alteroperator_02184_actor;

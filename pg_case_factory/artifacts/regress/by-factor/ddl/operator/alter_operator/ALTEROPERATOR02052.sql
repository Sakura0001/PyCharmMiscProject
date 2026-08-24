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
-- case_id: ALTEROPERATOR02052
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-EXT|02052|set_estimator|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperator_02052_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_02052_sch;
CREATE SCHEMA IF NOT EXISTS alteroperator_02052_target_sch;
CREATE FUNCTION alteroperator_02052_sch.alteroperator_02052_op_proc(l boolean, r boolean) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR alteroperator_02052_sch.#~ (boolean, boolean) SET (RESTRICT = NONE);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42883
-- 4. 断言与目录审计。
SELECT count(*) AS op_present FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'boolean'::regtype AND oprright = 'boolean'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_02052_sch') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperator_02052_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_02052_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_02052_sch.alteroperator_02052_op_proc CASCADE;

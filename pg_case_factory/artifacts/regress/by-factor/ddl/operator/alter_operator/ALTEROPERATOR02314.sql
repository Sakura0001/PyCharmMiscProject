-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR branch_set_estimator=bounded_cross_branch_set_estimator_catalog_query_drop_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR02314
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-EXT|02314|set_estimator|catalog_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperator_02314_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_02314_sch;
CREATE SCHEMA IF NOT EXISTS alteroperator_02314_target_sch;
CREATE FUNCTION alteroperator_02314_sch.alteroperator_02314_op_proc(l integer, r integer) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE OPERATOR alteroperator_02314_sch.#~ ( PROCEDURE = alteroperator_02314_sch.alteroperator_02314_op_proc, LEFTARG = integer, RIGHTARG = integer );
-- primary-target-begin
ALTER OPERATOR alteroperator_02314_sch.#~ (integer, integer) SET (RESTRICT = eqsel);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=00000
-- 4. 断言与目录审计。
SELECT count(*) AS op_present FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_02314_sch') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperator_02314_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_02314_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_02314_sch.alteroperator_02314_op_proc CASCADE;

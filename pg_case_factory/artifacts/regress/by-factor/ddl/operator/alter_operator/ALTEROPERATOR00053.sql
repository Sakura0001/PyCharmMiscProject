-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER OPERATOR schema_migration_state=target_schema_missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATOR00053
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/alter_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/alter_operator.yaml
-- primary_obligation_id: AO-SFV|sfv-03f57fa88ce850f108498386|set_schema
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperator_00053_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperator_00053_sch;
CREATE FUNCTION alteroperator_00053_sch.alteroperator_00053_op_proc(l integer, r integer) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;
CREATE OPERATOR alteroperator_00053_sch.#~ ( PROCEDURE = alteroperator_00053_sch.alteroperator_00053_op_proc, LEFTARG = integer, RIGHTARG = integer );
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR alteroperator_00053_sch.#~ (integer, integer) SET SCHEMA alteroperator_00053_target_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=3F000
-- 4. 断言与目录审计。
SELECT count(*) AS op_schema_changed FROM pg_catalog.pg_operator WHERE oprname = '#~' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype AND oprnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperator_00053_target_sch') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperator_00053_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperator_00053_target_sch CASCADE;
DROP FUNCTION IF EXISTS alteroperator_00053_sch.alteroperator_00053_op_proc CASCADE;

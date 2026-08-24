-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST target_action=with_function
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST12895
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|12895|actual_cast_execution|DROP_CAST_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_12895_sourcetype AS boolean);
DROP CAST IF EXISTS (boolean AS createcast_12895_sourcetype);
DROP FUNCTION IF EXISTS createcast_12895_castfn;
DROP FUNCTION IF EXISTS createcast_12895_revcastfn;
DROP TYPE IF EXISTS createcast_12895_sourcetype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_12895_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_12895_castfn(createcast_12895_sourcetype) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::boolean $$;
CREATE FUNCTION createcast_12895_revcastfn(boolean) RETURNS createcast_12895_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_12895_sourcetype $$;
CREATE CAST (boolean AS createcast_12895_sourcetype) WITH FUNCTION createcast_12895_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_12895_sourcetype AS boolean) WITH FUNCTION createcast_12895_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT NULL::createcast_12895_sourcetype::boolean AS cast_execution_check;
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (createcast_12895_sourcetype AS boolean);
DROP CAST IF EXISTS (boolean AS createcast_12895_sourcetype);
DROP FUNCTION IF EXISTS createcast_12895_castfn;
DROP FUNCTION IF EXISTS createcast_12895_revcastfn;
DROP TYPE IF EXISTS createcast_12895_sourcetype;

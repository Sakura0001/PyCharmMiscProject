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
-- case_id: CREATECAST12959
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|12959|actual_cast_execution|DROP_CAST_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (integer AS createcast_12959_targettype);
DROP CAST IF EXISTS (createcast_12959_targettype AS integer);
DROP FUNCTION IF EXISTS createcast_12959_castfn;
DROP FUNCTION IF EXISTS createcast_12959_revcastfn;
DROP TYPE IF EXISTS createcast_12959_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_12959_targettype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_12959_castfn(integer) RETURNS createcast_12959_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_12959_targettype $$;
CREATE FUNCTION createcast_12959_revcastfn(createcast_12959_targettype) RETURNS integer LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::integer $$;
CREATE CAST (createcast_12959_targettype AS integer) WITH FUNCTION createcast_12959_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (integer AS createcast_12959_targettype) WITH FUNCTION createcast_12959_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT NULL::integer::createcast_12959_targettype AS cast_execution_check;
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (integer AS createcast_12959_targettype);
DROP CAST IF EXISTS (createcast_12959_targettype AS integer);
DROP FUNCTION IF EXISTS createcast_12959_castfn;
DROP FUNCTION IF EXISTS createcast_12959_revcastfn;
DROP TYPE IF EXISTS createcast_12959_targettype;

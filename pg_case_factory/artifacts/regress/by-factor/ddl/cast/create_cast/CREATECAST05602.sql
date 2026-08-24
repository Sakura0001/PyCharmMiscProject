-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST function_dependency=function_exists_wrong_signature
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST05602
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|05602|actual_cast_execution|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_05602_sourcetype AS float8);
DROP CAST IF EXISTS (float8 AS createcast_05602_sourcetype);
DROP FUNCTION IF EXISTS public.createcast_05602_castfn;
DROP FUNCTION IF EXISTS createcast_05602_revcastfn;
DROP TYPE IF EXISTS createcast_05602_sourcetype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_05602_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION public.createcast_05602_castfn(float8) RETURNS float8 LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::float8 $$;
CREATE FUNCTION createcast_05602_revcastfn(float8) RETURNS createcast_05602_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_05602_sourcetype $$;
CREATE CAST (float8 AS createcast_05602_sourcetype) WITH FUNCTION createcast_05602_revcastfn;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_05602_sourcetype AS float8) WITH FUNCTION public.createcast_05602_castfn AS ASSIGNMENT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP CAST (createcast_05602_sourcetype AS float8);
DROP CAST (float8 AS createcast_05602_sourcetype);
DROP FUNCTION IF EXISTS public.createcast_05602_castfn;
DROP FUNCTION IF EXISTS createcast_05602_revcastfn;
DROP TYPE IF EXISTS createcast_05602_sourcetype;

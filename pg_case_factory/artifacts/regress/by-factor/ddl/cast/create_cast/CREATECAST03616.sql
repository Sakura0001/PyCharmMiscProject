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
-- case_id: CREATECAST03616
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|03616|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (integer AS numeric);
DROP CAST IF EXISTS (numeric AS integer);
DROP FUNCTION IF EXISTS createcast_03616_castfn;
DROP FUNCTION IF EXISTS createcast_03616_revcastfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createcast_03616_castfn(numeric) RETURNS numeric LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::numeric $$;
CREATE FUNCTION createcast_03616_revcastfn(numeric) RETURNS integer LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::integer $$;
CREATE CAST (numeric AS integer) WITH FUNCTION createcast_03616_revcastfn;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (integer AS numeric) WITH FUNCTION createcast_03616_castfn AS ASSIGNMENT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'integer'::regtype AND casttarget = 'numeric'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST (integer AS numeric);
DROP CAST (numeric AS integer);
DROP FUNCTION IF EXISTS createcast_03616_castfn;
DROP FUNCTION IF EXISTS createcast_03616_revcastfn;

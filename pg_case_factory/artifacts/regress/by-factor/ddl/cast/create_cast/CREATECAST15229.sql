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
-- case_id: CREATECAST15229
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|15229|pg_cast_catalog_query|DROP_CAST_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (integer AS bigint);
DROP CAST IF EXISTS (bigint AS integer);
DROP FUNCTION IF EXISTS public.createcast_15229_castfn;
DROP FUNCTION IF EXISTS createcast_15229_revcastfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION public.createcast_15229_castfn(integer) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::bigint $$;
CREATE FUNCTION createcast_15229_revcastfn(bigint) RETURNS integer LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::integer $$;
CREATE CAST (bigint AS integer) WITH FUNCTION createcast_15229_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (integer AS bigint) WITH FUNCTION public.createcast_15229_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'integer'::regtype AND casttarget = 'bigint'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (integer AS bigint);
DROP CAST IF EXISTS (bigint AS integer);
DROP FUNCTION IF EXISTS public.createcast_15229_castfn;
DROP FUNCTION IF EXISTS createcast_15229_revcastfn;

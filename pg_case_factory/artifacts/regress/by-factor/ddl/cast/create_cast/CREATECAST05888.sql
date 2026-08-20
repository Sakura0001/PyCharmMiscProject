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
-- case_id: CREATECAST05888
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|05888|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (integer AS createcast_05888_targettype);
DROP CAST IF EXISTS (createcast_05888_targettype AS integer);
DROP FUNCTION IF EXISTS public.createcast_05888_castfn;
DROP FUNCTION IF EXISTS createcast_05888_revcastfn;
DROP TYPE IF EXISTS createcast_05888_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_05888_targettype AS ENUM ('a', 'b');
CREATE FUNCTION public.createcast_05888_castfn(createcast_05888_targettype) RETURNS createcast_05888_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_05888_targettype $$;
CREATE FUNCTION createcast_05888_revcastfn(createcast_05888_targettype) RETURNS integer LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::integer $$;
CREATE CAST (createcast_05888_targettype AS integer) WITH FUNCTION createcast_05888_revcastfn;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (integer AS createcast_05888_targettype) WITH FUNCTION public.createcast_05888_castfn AS ASSIGNMENT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'integer'::regtype AND casttarget = 'createcast_05888_targettype'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST (integer AS createcast_05888_targettype);
DROP CAST (createcast_05888_targettype AS integer);
DROP FUNCTION IF EXISTS public.createcast_05888_castfn;
DROP FUNCTION IF EXISTS createcast_05888_revcastfn;
DROP TYPE IF EXISTS createcast_05888_targettype;

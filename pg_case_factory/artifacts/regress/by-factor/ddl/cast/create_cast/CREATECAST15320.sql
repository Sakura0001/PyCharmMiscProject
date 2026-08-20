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
-- case_id: CREATECAST15320
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|15320|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (timestamp AS createcast_15320_targettype);
DROP CAST IF EXISTS (createcast_15320_targettype AS timestamp);
DROP FUNCTION IF EXISTS public.createcast_15320_castfn;
DROP FUNCTION IF EXISTS createcast_15320_revcastfn;
DROP TYPE IF EXISTS createcast_15320_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_15320_targettype AS ENUM ('a', 'b');
CREATE FUNCTION public.createcast_15320_castfn(timestamp) RETURNS createcast_15320_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_15320_targettype $$;
CREATE FUNCTION createcast_15320_revcastfn(createcast_15320_targettype) RETURNS timestamp LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::timestamp $$;
CREATE CAST (createcast_15320_targettype AS timestamp) WITH FUNCTION createcast_15320_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (timestamp AS createcast_15320_targettype) WITH FUNCTION public.createcast_15320_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'timestamp'::regtype AND casttarget = 'createcast_15320_targettype'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST (timestamp AS createcast_15320_targettype);
DROP CAST (createcast_15320_targettype AS timestamp);
DROP FUNCTION IF EXISTS public.createcast_15320_castfn;
DROP FUNCTION IF EXISTS createcast_15320_revcastfn;
DROP TYPE IF EXISTS createcast_15320_targettype;

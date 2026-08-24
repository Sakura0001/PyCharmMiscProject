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
-- case_id: CREATECAST14737
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|14737|pg_cast_catalog_query|DROP_CAST_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_14737_sourcetype AS timestamp);
DROP CAST IF EXISTS (timestamp AS createcast_14737_sourcetype);
DROP FUNCTION IF EXISTS public.createcast_14737_castfn;
DROP FUNCTION IF EXISTS createcast_14737_revcastfn;
DROP TYPE IF EXISTS createcast_14737_sourcetype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_14737_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION public.createcast_14737_castfn(createcast_14737_sourcetype) RETURNS timestamp LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::timestamp $$;
CREATE FUNCTION createcast_14737_revcastfn(timestamp) RETURNS createcast_14737_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_14737_sourcetype $$;
CREATE CAST (timestamp AS createcast_14737_sourcetype) WITH FUNCTION createcast_14737_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_14737_sourcetype AS timestamp) WITH FUNCTION public.createcast_14737_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'createcast_14737_sourcetype'::regtype AND casttarget = 'timestamp'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (createcast_14737_sourcetype AS timestamp);
DROP CAST IF EXISTS (timestamp AS createcast_14737_sourcetype);
DROP FUNCTION IF EXISTS public.createcast_14737_castfn;
DROP FUNCTION IF EXISTS createcast_14737_revcastfn;
DROP TYPE IF EXISTS createcast_14737_sourcetype;

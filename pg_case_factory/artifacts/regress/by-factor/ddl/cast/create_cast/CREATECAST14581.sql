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
-- case_id: CREATECAST14581
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|14581|pg_cast_catalog_query|DROP_CAST_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (numeric AS createcast_14581_targettype);
DROP CAST IF EXISTS (createcast_14581_targettype AS numeric);
DROP FUNCTION IF EXISTS public.createcast_14581_castfn;
DROP FUNCTION IF EXISTS createcast_14581_revcastfn;
DROP TYPE IF EXISTS createcast_14581_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_14581_targettype AS ENUM ('a', 'b');
CREATE FUNCTION public.createcast_14581_castfn(numeric) RETURNS createcast_14581_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_14581_targettype $$;
CREATE FUNCTION createcast_14581_revcastfn(createcast_14581_targettype) RETURNS numeric LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::numeric $$;
CREATE CAST (createcast_14581_targettype AS numeric) WITH FUNCTION createcast_14581_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (numeric AS createcast_14581_targettype) WITH FUNCTION public.createcast_14581_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'numeric'::regtype AND casttarget = 'createcast_14581_targettype'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (numeric AS createcast_14581_targettype);
DROP CAST IF EXISTS (createcast_14581_targettype AS numeric);
DROP FUNCTION IF EXISTS public.createcast_14581_castfn;
DROP FUNCTION IF EXISTS createcast_14581_revcastfn;
DROP TYPE IF EXISTS createcast_14581_targettype;

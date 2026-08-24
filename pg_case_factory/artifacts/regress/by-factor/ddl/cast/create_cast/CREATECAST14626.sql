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
-- case_id: CREATECAST14626
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|14626|actual_cast_execution|DROP_CAST
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (text AS timestamp);
DROP CAST IF EXISTS (timestamp AS text);
DROP FUNCTION IF EXISTS public.createcast_14626_castfn;
DROP FUNCTION IF EXISTS createcast_14626_revcastfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION public.createcast_14626_castfn(text) RETURNS timestamp LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::timestamp $$;
CREATE FUNCTION createcast_14626_revcastfn(timestamp) RETURNS text LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::text $$;
CREATE CAST (timestamp AS text) WITH FUNCTION createcast_14626_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (text AS timestamp) WITH FUNCTION public.createcast_14626_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT NULL::text::timestamp AS cast_execution_check;
-- 5. 清理全部本编号对象。
DROP CAST (text AS timestamp);
DROP CAST (timestamp AS text);
DROP FUNCTION IF EXISTS public.createcast_14626_castfn;
DROP FUNCTION IF EXISTS createcast_14626_revcastfn;

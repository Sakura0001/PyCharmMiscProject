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
-- case_id: CREATECAST13361
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|13361|pg_cast_catalog_query|DROP_CAST_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_13361_sourcetype AS numeric);
DROP CAST IF EXISTS (numeric AS createcast_13361_sourcetype);
DROP FUNCTION IF EXISTS createcast_13361_castfn;
DROP FUNCTION IF EXISTS createcast_13361_revcastfn;
DROP TYPE IF EXISTS createcast_13361_sourcetype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_13361_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_13361_castfn(createcast_13361_sourcetype) RETURNS numeric LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::numeric $$;
CREATE FUNCTION createcast_13361_revcastfn(numeric) RETURNS createcast_13361_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_13361_sourcetype $$;
CREATE CAST (numeric AS createcast_13361_sourcetype) WITH FUNCTION createcast_13361_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_13361_sourcetype AS numeric) WITH FUNCTION createcast_13361_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'createcast_13361_sourcetype'::regtype AND casttarget = 'numeric'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (createcast_13361_sourcetype AS numeric);
DROP CAST IF EXISTS (numeric AS createcast_13361_sourcetype);
DROP FUNCTION IF EXISTS createcast_13361_castfn;
DROP FUNCTION IF EXISTS createcast_13361_revcastfn;
DROP TYPE IF EXISTS createcast_13361_sourcetype;

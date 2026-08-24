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
-- case_id: CREATECAST05173
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|05173|pg_cast_catalog_query|DROP_CAST_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (date AS createcast_05173_targettype);
DROP CAST IF EXISTS (createcast_05173_targettype AS date);
DROP FUNCTION IF EXISTS createcast_05173_castfn;
DROP FUNCTION IF EXISTS createcast_05173_revcastfn;
DROP TYPE IF EXISTS createcast_05173_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_05173_targettype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_05173_castfn(createcast_05173_targettype) RETURNS createcast_05173_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_05173_targettype $$;
CREATE FUNCTION createcast_05173_revcastfn(createcast_05173_targettype) RETURNS date LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::date $$;
CREATE CAST (createcast_05173_targettype AS date) WITH FUNCTION createcast_05173_revcastfn;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (date AS createcast_05173_targettype) WITH FUNCTION createcast_05173_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'date'::regtype AND casttarget = 'createcast_05173_targettype'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (date AS createcast_05173_targettype);
DROP CAST IF EXISTS (createcast_05173_targettype AS date);
DROP FUNCTION IF EXISTS createcast_05173_castfn;
DROP FUNCTION IF EXISTS createcast_05173_revcastfn;
DROP TYPE IF EXISTS createcast_05173_targettype;

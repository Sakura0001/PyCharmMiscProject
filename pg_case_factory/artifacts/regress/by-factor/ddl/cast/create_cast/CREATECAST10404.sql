-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST function_dependency=function_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST10404
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|10404|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_10404_sourcetype AS timestamp);
DROP CAST IF EXISTS (timestamp AS createcast_10404_sourcetype);
DROP FUNCTION IF EXISTS createcast_10404_revcastfn;
DROP TYPE IF EXISTS createcast_10404_sourcetype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_10404_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_10404_revcastfn(timestamp) RETURNS createcast_10404_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_10404_sourcetype $$;
CREATE CAST (timestamp AS createcast_10404_sourcetype) WITH FUNCTION createcast_10404_revcastfn;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_10404_sourcetype AS timestamp) WITH FUNCTION createcast_10404_nonexistfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'createcast_10404_sourcetype'::regtype AND casttarget = 'timestamp'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST (createcast_10404_sourcetype AS timestamp);
DROP CAST (timestamp AS createcast_10404_sourcetype);
DROP FUNCTION IF EXISTS createcast_10404_revcastfn;
DROP TYPE IF EXISTS createcast_10404_sourcetype;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE target_action=regular
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE02852
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|02852|pg_aggregate_catalog_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS "createaggregate_02852_Mixed Agg"(timestamp);
DROP FUNCTION IF EXISTS createaggregate_02852_nsp.createaggregate_02852_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_02852_ffunc(timestamp);
DROP FUNCTION IF EXISTS createaggregate_02852_combine(timestamp, timestamp);
DROP SCHEMA IF EXISTS createaggregate_02852_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_02852_nsp;
CREATE FUNCTION createaggregate_02852_nsp.createaggregate_02852_sfunc(text, text) RETURNS timestamp AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_02852_ffunc(timestamp) RETURNS timestamp AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_02852_combine(timestamp, timestamp) RETURNS timestamp AS $$ SELECT $1 $$ LANGUAGE SQL;
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE "createaggregate_02852_Mixed Agg" (timestamp, timestamp) (SFUNC = createaggregate_02852_nsp.createaggregate_02852_sfunc, STYPE = timestamp, FINALFUNC = createaggregate_02852_ffunc, COMBINEFUNC = createaggregate_02852_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'createaggregate_02852_Mixed Agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS "createaggregate_02852_Mixed Agg"(timestamp);
DROP FUNCTION IF EXISTS createaggregate_02852_nsp.createaggregate_02852_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_02852_ffunc(timestamp);
DROP FUNCTION IF EXISTS createaggregate_02852_combine(timestamp, timestamp);
DROP SCHEMA IF EXISTS createaggregate_02852_nsp CASCADE;

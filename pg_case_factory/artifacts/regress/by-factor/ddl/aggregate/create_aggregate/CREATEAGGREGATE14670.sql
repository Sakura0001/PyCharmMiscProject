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
-- case_id: CREATEAGGREGATE14670
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|14670|pg_aggregate_catalog_query|DROP_AGGREGATE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE "createaggregate_14670_Mixed Agg" CASCADE;
DROP FUNCTION IF EXISTS createaggregate_14670_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_14670_ffunc(bigint);
DROP FUNCTION IF EXISTS createaggregate_14670_combine(bigint, bigint);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaggregate_14670_sfunc(text, text) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_14670_ffunc(bigint) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_14670_combine(bigint, bigint) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "createaggregate_14670_Mixed Agg" () (SFUNC = createaggregate_14670_sfunc, STYPE = bigint, FINALFUNC = createaggregate_14670_ffunc, COMBINEFUNC = createaggregate_14670_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'createaggregate_14670_Mixed Agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE "createaggregate_14670_Mixed Agg" CASCADE;
DROP FUNCTION IF EXISTS createaggregate_14670_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_14670_ffunc(bigint);
DROP FUNCTION IF EXISTS createaggregate_14670_combine(bigint, bigint);

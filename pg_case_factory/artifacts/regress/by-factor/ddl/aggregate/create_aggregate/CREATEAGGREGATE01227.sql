-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE01227
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|01227|pg_proc_query|DROP_AGGREGATE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_01227_agg(text) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_01227_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01227_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_01227_combine(text, text);
DROP OWNED BY createaggregate_01227_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_01227_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createaggregate_01227_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_01227_actor;
CREATE FUNCTION createaggregate_01227_sfunc(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01227_ffunc(text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01227_combine(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_01227_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE createaggregate_01227_agg (text, text) (SFUNC = createaggregate_01227_sfunc, STYPE = text, FINALFUNC = createaggregate_01227_ffunc, COMBINEFUNC = createaggregate_01227_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'createaggregate_01227_agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE createaggregate_01227_agg(text) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_01227_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01227_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_01227_combine(text, text);
DROP OWNED BY createaggregate_01227_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_01227_actor;

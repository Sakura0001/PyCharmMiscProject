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
-- case_id: CREATEAGGREGATE03107
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|03107|pg_proc_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS "order"(bigint);
DROP FUNCTION IF EXISTS createaggregate_03107_nsp.createaggregate_03107_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_03107_ffunc(bigint);
DROP FUNCTION IF EXISTS createaggregate_03107_combine(bigint, bigint);
DROP OWNED BY createaggregate_03107_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_03107_actor;
DROP SCHEMA IF EXISTS createaggregate_03107_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_03107_nsp;
CREATE ROLE createaggregate_03107_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_03107_actor;
GRANT USAGE ON SCHEMA createaggregate_03107_nsp TO createaggregate_03107_actor;
CREATE FUNCTION createaggregate_03107_nsp.createaggregate_03107_sfunc(text, text) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_03107_ffunc(bigint) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_03107_combine(bigint, bigint) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_03107_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE "order" (bigint, bigint) (SFUNC = createaggregate_03107_nsp.createaggregate_03107_sfunc, STYPE = bigint, FINALFUNC = createaggregate_03107_ffunc, COMBINEFUNC = createaggregate_03107_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'order' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS "order"(bigint);
DROP FUNCTION IF EXISTS createaggregate_03107_nsp.createaggregate_03107_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_03107_ffunc(bigint);
DROP FUNCTION IF EXISTS createaggregate_03107_combine(bigint, bigint);
DROP OWNED BY createaggregate_03107_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_03107_actor;
DROP SCHEMA IF EXISTS createaggregate_03107_nsp CASCADE;

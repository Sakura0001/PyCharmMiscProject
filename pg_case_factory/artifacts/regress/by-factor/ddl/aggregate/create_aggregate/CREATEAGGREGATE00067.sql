-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE verification_mode=actual_execution
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE00067
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-SFV|sfv-cbeebcf815c304e6bb8800e0|regular
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_00067_agg(integer);
DROP FUNCTION IF EXISTS createaggregate_00067_sfunc(integer, integer);
DROP FUNCTION IF EXISTS createaggregate_00067_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_00067_combine(integer, integer);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaggregate_00067_sfunc(integer, integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_00067_ffunc(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_00067_combine(integer, integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE createaggregate_00067_agg (integer) (SFUNC = createaggregate_00067_sfunc, STYPE = integer, FINALFUNC = createaggregate_00067_ffunc, COMBINEFUNC = createaggregate_00067_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_executable FROM (SELECT createaggregate_00067_agg(NULL::integer) AS r) s ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE createaggregate_00067_agg(integer);
DROP FUNCTION IF EXISTS createaggregate_00067_sfunc(integer, integer);
DROP FUNCTION IF EXISTS createaggregate_00067_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_00067_combine(integer, integer);

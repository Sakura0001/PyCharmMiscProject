-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : VACUUM environment_context=transaction_block
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: VACUUM01356
-- source_md: skills/pg-sql-generation/references/statements/utility/maintenance/vacuum.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/maintenance/vacuum.yaml
-- primary_obligation_id: VACUUM-EXT|01356|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS vacuum_01356_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE vacuum_01356_t (id integer);
BEGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 VACUUM。
-- primary-target-begin
VACUUM (BUFFER_USAGE_LIMIT '16MB') "vacuum_01356_t";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
SELECT count(*) AS catalog_relation_count FROM pg_catalog.pg_class c WHERE c.relname = 'vacuum_01356_t' AND c.relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS vacuum_01356_t CASCADE;

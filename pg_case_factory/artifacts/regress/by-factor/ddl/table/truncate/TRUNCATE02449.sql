-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : TRUNCATE object_state=table_does_not_exist
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: TRUNCATE02449
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/truncate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/truncate.yaml
-- primary_obligation_id: TRUNCATE-EXT|02449|select_count_zero|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS truncate_02449_tbl, truncate_02449_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS target_relation_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 TRUNCATE。
-- primary-target-begin
TRUNCATE TABLE truncate_02449_missing ;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_state FROM pg_catalog.pg_class WHERE relname = 'truncate_02449_missing' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS truncate_02449_tbl, truncate_02449_ref CASCADE;

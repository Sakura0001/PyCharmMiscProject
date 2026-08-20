-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DEALLOCATE prepared_state=missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DEALLOCATE03081
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/deallocate.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/deallocate.yaml
-- primary_obligation_id: DEALLOC-EXT|03081|catalog_query|reset_state|behavior_lifecycle
-- expected_outcome: expected_failure
-- expected_sqlstate: 26000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS deallocate_03081_schema.deallocate_03081_base, deallocate_03081_schema.deallocate_03081_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS deallocate_03081_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA deallocate_03081_schema;
CREATE TABLE deallocate_03081_schema.deallocate_03081_base (c1 int, c2 text);
INSERT INTO deallocate_03081_schema.deallocate_03081_base VALUES (1, 'hello');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DEALLOCATE。
-- primary-target-begin
DEALLOCATE deallocate_03081_nonexistent;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '26000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS stmt_state FROM pg_catalog.pg_prepared_statements ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DEALLOCATE ALL;
DROP TABLE IF EXISTS deallocate_03081_schema.deallocate_03081_base CASCADE;
DROP TABLE IF EXISTS deallocate_03081_schema.deallocate_03081_target CASCADE;
DROP SCHEMA IF EXISTS deallocate_03081_schema CASCADE;
DROP TABLE IF EXISTS deallocate_03081_schema.deallocate_03081_base, deallocate_03081_schema.deallocate_03081_target CASCADE;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DEALLOCATE dependency_state=missing_dependency
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DEALLOCATE05833
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/deallocate.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/deallocate.yaml
-- primary_obligation_id: DEALLOC-EXT|05833|returned_rows|rollback|full_cross
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS deallocate_05833_schema.deallocate_05833_base, deallocate_05833_schema.deallocate_05833_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS deallocate_05833_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA deallocate_05833_schema;
CREATE TABLE deallocate_05833_schema.deallocate_05833_base (c1 int, c2 text);
INSERT INTO deallocate_05833_schema.deallocate_05833_base VALUES (1, 'hello');
CREATE TABLE deallocate_05833_schema.deallocate_05833_target (c1 int, c2 text);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DEALLOCATE。
-- primary-target-begin
DEALLOCATE deallocate_05833_nonexistent;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS deallocate_05833_schema.deallocate_05833_base CASCADE;
DROP TABLE IF EXISTS deallocate_05833_schema.deallocate_05833_target CASCADE;
DROP SCHEMA IF EXISTS deallocate_05833_schema CASCADE;
DROP TABLE IF EXISTS deallocate_05833_schema.deallocate_05833_base, deallocate_05833_schema.deallocate_05833_target CASCADE;

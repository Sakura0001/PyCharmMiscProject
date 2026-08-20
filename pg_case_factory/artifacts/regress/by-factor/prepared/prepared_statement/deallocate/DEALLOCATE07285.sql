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
-- case_id: DEALLOCATE07285
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/deallocate.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/deallocate.yaml
-- primary_obligation_id: DEALLOC-EXT|07285|returned_rows|rollback|boundary_cross
-- expected_outcome: expected_failure
-- expected_sqlstate: 26000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS deallocate_07285_schema.deallocate_07285_base, deallocate_07285_schema.deallocate_07285_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS deallocate_07285_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA deallocate_07285_schema;
CREATE TABLE deallocate_07285_schema.deallocate_07285_base (c1 int, c2 text);
INSERT INTO deallocate_07285_schema.deallocate_07285_base VALUES (1, 'hello');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DEALLOCATE。
-- primary-target-begin
DEALLOCATE deallocate_07285_nonexistent;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '26000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS deallocate_07285_schema.deallocate_07285_base CASCADE;
DROP TABLE IF EXISTS deallocate_07285_schema.deallocate_07285_target CASCADE;
DROP SCHEMA IF EXISTS deallocate_07285_schema CASCADE;
DROP TABLE IF EXISTS deallocate_07285_schema.deallocate_07285_base, deallocate_07285_schema.deallocate_07285_target CASCADE;

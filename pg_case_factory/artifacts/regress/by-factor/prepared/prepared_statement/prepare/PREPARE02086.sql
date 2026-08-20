-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : PREPARE argument_shape=wrong_type_arguments
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: PREPARE02086
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/prepare.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/prepare.yaml
-- primary_obligation_id: PREPARE-EXT|02086|effect_query|rollback|naming_argument
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS prepare_02086_schema.prepare_02086_base, prepare_02086_schema.prepare_02086_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS prepare_02086_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA prepare_02086_schema;
CREATE TABLE prepare_02086_schema.prepare_02086_base (c1 int, c2 text);
INSERT INTO prepare_02086_schema.prepare_02086_base VALUES (1, 'hello');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 PREPARE。
-- primary-target-begin
PREPARE prepare_02086_nonexistent AS SELECT * FROM prepare_02086_nonexistent_table;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS prepare_02086_schema.prepare_02086_base CASCADE;
DROP TABLE IF EXISTS prepare_02086_schema.prepare_02086_target CASCADE;
DROP SCHEMA IF EXISTS prepare_02086_schema CASCADE;
DROP TABLE IF EXISTS prepare_02086_schema.prepare_02086_base, prepare_02086_schema.prepare_02086_target CASCADE;

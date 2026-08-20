-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : PREPARE expected_status=success
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: PREPARE00013
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/prepare.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/prepare.yaml
-- primary_obligation_id: PREPARE-SFV|sfv-c0b4f94a8775bff3d8bdef58|prepare_statement
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS prepare_00013_schema.prepare_00013_base, prepare_00013_schema.prepare_00013_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS prepare_00013_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA prepare_00013_schema;
CREATE TABLE prepare_00013_schema.prepare_00013_base (c1 int, c2 text);
INSERT INTO prepare_00013_schema.prepare_00013_base VALUES (1, 'hello');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 PREPARE。
-- primary-target-begin
PREPARE prepare_00013_stmt AS SELECT * FROM prepare_00013_schema.prepare_00013_base;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stmt_state FROM pg_catalog.pg_prepared_statements ORDER BY count(*) LIMIT 1;
EXECUTE prepare_00013_stmt;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS prepare_00013_schema.prepare_00013_base CASCADE;
DROP TABLE IF EXISTS prepare_00013_schema.prepare_00013_target CASCADE;
DROP SCHEMA IF EXISTS prepare_00013_schema CASCADE;
DROP TABLE IF EXISTS prepare_00013_schema.prepare_00013_base, prepare_00013_schema.prepare_00013_target CASCADE;

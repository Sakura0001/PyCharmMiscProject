-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : PREPARE target_form=prepare_statement
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: PREPARE02916
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/prepare.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/prepare.yaml
-- primary_obligation_id: PREPARE-EXT|02916|effect_query|reset_state|behavior_lifecycle
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS prepare_02916_schema.prepare_02916_base, prepare_02916_schema.prepare_02916_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS prepare_02916_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA prepare_02916_schema;
CREATE TABLE prepare_02916_schema.prepare_02916_base (c1 int, c2 text);
INSERT INTO prepare_02916_schema.prepare_02916_base VALUES (1, 'hello');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 PREPARE。
-- primary-target-begin
PREPARE prepare_02916_stmt (int) AS SELECT $1::text FROM prepare_02916_schema.prepare_02916_base;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
DEALLOCATE ALL;
-- 5. 清理全部本编号对象。
RESET ROLE;
DEALLOCATE ALL;
DROP TABLE IF EXISTS prepare_02916_schema.prepare_02916_base CASCADE;
DROP TABLE IF EXISTS prepare_02916_schema.prepare_02916_target CASCADE;
DROP SCHEMA IF EXISTS prepare_02916_schema CASCADE;
DROP TABLE IF EXISTS prepare_02916_schema.prepare_02916_base, prepare_02916_schema.prepare_02916_target CASCADE;

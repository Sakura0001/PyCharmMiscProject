-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DEALLOCATE target_form=deallocate_statement
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DEALLOCATE05532
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/deallocate.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/deallocate.yaml
-- primary_obligation_id: DEALLOC-EXT|05532|effect_query|reset_state|full_cross
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS deallocate_05532_schema.deallocate_05532_base, deallocate_05532_schema.deallocate_05532_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS deallocate_05532_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA deallocate_05532_schema;
CREATE TABLE deallocate_05532_schema.deallocate_05532_base (c1 int, c2 text);
INSERT INTO deallocate_05532_schema.deallocate_05532_base VALUES (1, 'hello');
CREATE TABLE deallocate_05532_schema.deallocate_05532_target (c1 int, c2 text);
PREPARE "deallocate_05532_Stmt" (int, text) AS INSERT INTO deallocate_05532_schema.deallocate_05532_target VALUES ($1, $2);
EXECUTE "deallocate_05532_Stmt";
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DEALLOCATE。
-- primary-target-begin
DEALLOCATE "deallocate_05532_Stmt";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_observed FROM pg_catalog.pg_prepared_statements WHERE name = '"deallocate_05532_Stmt"' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DEALLOCATE ALL;
DROP TABLE IF EXISTS deallocate_05532_schema.deallocate_05532_base CASCADE;
DROP TABLE IF EXISTS deallocate_05532_schema.deallocate_05532_target CASCADE;
DROP SCHEMA IF EXISTS deallocate_05532_schema CASCADE;
DROP TABLE IF EXISTS deallocate_05532_schema.deallocate_05532_base, deallocate_05532_schema.deallocate_05532_target CASCADE;

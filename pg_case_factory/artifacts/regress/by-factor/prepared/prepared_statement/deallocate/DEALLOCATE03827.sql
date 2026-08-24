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
-- case_id: DEALLOCATE03827
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/deallocate.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/deallocate.yaml
-- primary_obligation_id: DEALLOC-EXT|03827|effect_query|drop_objects|full_cross
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS deallocate_03827_schema.deallocate_03827_base, deallocate_03827_schema.deallocate_03827_target CASCADE;
DEALLOCATE ALL;
DROP SCHEMA IF EXISTS deallocate_03827_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA deallocate_03827_schema;
CREATE TABLE deallocate_03827_schema.deallocate_03827_base (c1 int, c2 text);
INSERT INTO deallocate_03827_schema.deallocate_03827_base VALUES (1, 'hello');
CREATE TABLE deallocate_03827_schema.deallocate_03827_target (c1 int, c2 text);
PREPARE deallocate_03827_stmt (int, text) AS INSERT INTO deallocate_03827_schema.deallocate_03827_target VALUES ($1, $2);
EXECUTE deallocate_03827_stmt;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DEALLOCATE。
-- primary-target-begin
DEALLOCATE deallocate_03827_stmt;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_observed FROM pg_catalog.pg_prepared_statements WHERE name = 'deallocate_03827_stmt' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DEALLOCATE ALL;
DROP TABLE IF EXISTS deallocate_03827_schema.deallocate_03827_base CASCADE;
DROP TABLE IF EXISTS deallocate_03827_schema.deallocate_03827_target CASCADE;
DROP SCHEMA IF EXISTS deallocate_03827_schema CASCADE;
DROP TABLE IF EXISTS deallocate_03827_schema.deallocate_03827_base, deallocate_03827_schema.deallocate_03827_target CASCADE;

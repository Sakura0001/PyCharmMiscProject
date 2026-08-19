-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP COLLATION object_state=already_exists_no_deps
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCOLLATION00110
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/drop_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/drop_collation.yaml
-- primary_obligation_id: DC-EXT|00110|drop_collation|pg_collation_removed_assertion|DROP_DEPENDENT_OBJECTS_FIRST
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropcollation_00110_t CASCADE;
DROP COLLATION IF EXISTS "dropcollation_00110_Quoted";
\set ON_ERROR_STOP on
-- 2. 创建完整本地排序规则和因子专用夹具。
CREATE COLLATION "dropcollation_00110_Quoted" (LC_COLLATE = 'C', LC_CTYPE = 'C');
CREATE TABLE dropcollation_00110_t (c text);
CREATE INDEX dropcollation_00110_idx ON dropcollation_00110_t (c COLLATE "dropcollation_00110_Quoted");
-- 3. 执行唯一获得覆盖信用的 DROP COLLATION。
-- primary-target-begin
DROP COLLATION IF EXISTS "dropcollation_00110_Quoted" CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS collation_absent FROM pg_catalog.pg_collation WHERE collname = 'dropcollation_00110_Quoted' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP COLLATION IF EXISTS "dropcollation_00110_Quoted" CASCADE;
DROP TABLE IF EXISTS dropcollation_00110_t CASCADE;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP COLLATION dependency_state=referenced_by_table_column
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCOLLATION00362
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/drop_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/drop_collation.yaml
-- primary_obligation_id: DC-EXT|00362|drop_collation|pg_collation_removed_assertion|DROP_DEPENDENT_OBJECTS_FIRST
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropcollation_00362_t CASCADE;
DROP COLLATION IF EXISTS dropcollation_00362_schema.dropcollation_00362_coll;
DROP SCHEMA IF EXISTS dropcollation_00362_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地排序规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropcollation_00362_schema;
CREATE COLLATION dropcollation_00362_schema.dropcollation_00362_coll (LC_COLLATE = 'C', LC_CTYPE = 'C');
CREATE TABLE dropcollation_00362_t (c text COLLATE dropcollation_00362_schema.dropcollation_00362_coll);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP COLLATION。
-- primary-target-begin
DROP COLLATION dropcollation_00362_schema.dropcollation_00362_coll RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS collation_present FROM pg_catalog.pg_collation WHERE collname = 'dropcollation_00362_coll' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP COLLATION IF EXISTS dropcollation_00362_schema.dropcollation_00362_coll CASCADE;
DROP SCHEMA IF EXISTS dropcollation_00362_schema CASCADE;
DROP TABLE IF EXISTS dropcollation_00362_t CASCADE;

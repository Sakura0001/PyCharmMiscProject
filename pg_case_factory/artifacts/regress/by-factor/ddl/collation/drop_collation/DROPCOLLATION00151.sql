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
-- case_id: DROPCOLLATION00151
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/drop_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/drop_collation.yaml
-- primary_obligation_id: DC-EXT|00151|drop_collation|pg_collation_catalog_query|DROP_COLLATION_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropcollation_00151_t CASCADE;
DROP COLLATION IF EXISTS dropcollation_00151_schema.dropcollation_00151_coll CASCADE;
DROP SCHEMA IF EXISTS dropcollation_00151_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地排序规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropcollation_00151_schema;
CREATE COLLATION dropcollation_00151_schema.dropcollation_00151_coll (LC_COLLATE = 'C', LC_CTYPE = 'C');
CREATE TABLE dropcollation_00151_t (c text);
CREATE INDEX dropcollation_00151_idx ON dropcollation_00151_t (c COLLATE dropcollation_00151_schema.dropcollation_00151_coll);
-- 3. 执行唯一获得覆盖信用的 DROP COLLATION。
-- primary-target-begin
DROP COLLATION dropcollation_00151_schema.dropcollation_00151_coll CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS collation_absent FROM pg_catalog.pg_collation WHERE collname = 'dropcollation_00151_coll' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP COLLATION IF EXISTS dropcollation_00151_schema.dropcollation_00151_coll CASCADE;
DROP SCHEMA IF EXISTS dropcollation_00151_schema CASCADE;
DROP TABLE IF EXISTS dropcollation_00151_t CASCADE;

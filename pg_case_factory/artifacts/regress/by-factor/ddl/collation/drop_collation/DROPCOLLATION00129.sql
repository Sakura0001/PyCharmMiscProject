-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP COLLATION privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCOLLATION00129
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/drop_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/drop_collation.yaml
-- primary_obligation_id: DC-EXT|00129|drop_collation|pg_collation_removed_assertion|DROP_COLLATION_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP COLLATION IF EXISTS dropcollation_00129_schema.dropcollation_00129_coll CASCADE;
DROP SCHEMA IF EXISTS dropcollation_00129_schema CASCADE;
DROP ROLE IF EXISTS dropcollation_00129_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地排序规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropcollation_00129_schema;
CREATE ROLE dropcollation_00129_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA dropcollation_00129_schema TO dropcollation_00129_actor;
CREATE COLLATION dropcollation_00129_schema.dropcollation_00129_coll (LC_COLLATE = 'C', LC_CTYPE = 'C');
SET ROLE dropcollation_00129_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP COLLATION。
-- primary-target-begin
DROP COLLATION dropcollation_00129_schema.dropcollation_00129_coll CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS collation_present FROM pg_catalog.pg_collation WHERE collname = 'dropcollation_00129_coll' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP COLLATION IF EXISTS dropcollation_00129_schema.dropcollation_00129_coll CASCADE;
DROP SCHEMA IF EXISTS dropcollation_00129_schema CASCADE;
DROP OWNED BY dropcollation_00129_actor;
DROP ROLE IF EXISTS dropcollation_00129_actor;

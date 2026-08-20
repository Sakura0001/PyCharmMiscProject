-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TYPE typed_table_dependency=has_typed_tables
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTYPE00089
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-SFV|sfv-c08dd464d3d8f6648a01ebc5|add_attribute
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertype_00089_t;
DROP TYPE IF EXISTS altertype_00089_type CASCADE;
DROP OWNED BY altertype_00089_owner CASCADE;
DROP ROLE IF EXISTS altertype_00089_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertype_00089_owner LOGIN;
SET ROLE altertype_00089_owner;
CREATE TYPE altertype_00089_type AS (altertype_00089_attr integer);
CREATE TABLE altertype_00089_t OF altertype_00089_type;
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_00089_type ADD ATTRIBUTE altertype_00089_attr integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM pg_catalog.pg_type WHERE typname = 'altertype_00089_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_00089_type CASCADE;
DROP OWNED BY altertype_00089_owner CASCADE;
DROP ROLE IF EXISTS altertype_00089_owner;
DROP TABLE IF EXISTS altertype_00089_t;

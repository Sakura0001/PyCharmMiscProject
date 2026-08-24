-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TYPE target_action=set_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTYPE08003
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|08003|pg_type_catalog_query|DROP_TYPE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS "altertype_08003_order" CASCADE;
DROP SCHEMA IF EXISTS altertype_08003_targetsch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertype_08003_targetsch;
GRANT CREATE ON SCHEMA altertype_08003_targetsch TO altertype_08003_owner;
CREATE TYPE "altertype_08003_order" AS (altertype_08003_attr integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE "altertype_08003_order" SET SCHEMA altertype_08003_targetsch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM pg_catalog.pg_type WHERE typname = 'altertype_08003_order' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS "altertype_08003_order" CASCADE;
DROP SCHEMA IF EXISTS altertype_08003_targetsch CASCADE;

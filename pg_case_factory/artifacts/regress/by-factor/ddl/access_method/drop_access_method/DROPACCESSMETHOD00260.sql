-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP ACCESS METHOD privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPACCESSMETHOD00260
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/drop_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/drop_access_method.yaml
-- primary_obligation_id: DAM-EXT|00260|drop_access_method|pg_am_catalog_query|DROP_ACCESS_METHOD_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropaccessmethod_00260_t CASCADE;
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00260_schema.dropaccessmethod_00260_am CASCADE;
DROP FUNCTION IF EXISTS dropaccessmethod_00260_amhandler;
DROP SCHEMA IF EXISTS dropaccessmethod_00260_schema CASCADE;
DROP ROLE IF EXISTS dropaccessmethod_00260_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地访问方法和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropaccessmethod_00260_schema;
CREATE ROLE dropaccessmethod_00260_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA dropaccessmethod_00260_schema TO dropaccessmethod_00260_actor;
CREATE FUNCTION dropaccessmethod_00260_amhandler(internal) RETURNS table_am_handler AS 'MODULE_PATHNAME' LANGUAGE C;
CREATE ACCESS METHOD dropaccessmethod_00260_schema.dropaccessmethod_00260_am TYPE TABLE HANDLER dropaccessmethod_00260_amhandler;
CREATE TABLE dropaccessmethod_00260_t (c integer);
CREATE INDEX dropaccessmethod_00260_idx ON dropaccessmethod_00260_t USING dropaccessmethod_00260_schema.dropaccessmethod_00260_am (c);
SET ROLE dropaccessmethod_00260_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ACCESS METHOD。
-- primary-target-begin
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00260_schema.dropaccessmethod_00260_am CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS access_method_present FROM pg_catalog.pg_am WHERE amname = 'dropaccessmethod_00260_am' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00260_schema.dropaccessmethod_00260_am CASCADE;
DROP FUNCTION IF EXISTS dropaccessmethod_00260_amhandler;
DROP SCHEMA IF EXISTS dropaccessmethod_00260_schema CASCADE;
DROP OWNED BY dropaccessmethod_00260_actor;
DROP ROLE IF EXISTS dropaccessmethod_00260_actor;
DROP TABLE IF EXISTS dropaccessmethod_00260_t CASCADE;

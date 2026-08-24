-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP ACCESS METHOD object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPACCESSMETHOD00271
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/drop_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/drop_access_method.yaml
-- primary_obligation_id: DAM-EXT|00271|drop_access_method|pg_am_removed_assertion|DROP_DEPENDENT_OBJECTS_FIRST
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropaccessmethod_00271_t CASCADE;
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00271_schema.dropaccessmethod_00271_am;
DROP FUNCTION IF EXISTS dropaccessmethod_00271_amhandler;
DROP SCHEMA IF EXISTS dropaccessmethod_00271_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地访问方法和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropaccessmethod_00271_schema;
CREATE FUNCTION dropaccessmethod_00271_amhandler(internal) RETURNS table_am_handler AS 'MODULE_PATHNAME' LANGUAGE C;
CREATE ACCESS METHOD dropaccessmethod_00271_schema.dropaccessmethod_00271_am TYPE TABLE HANDLER dropaccessmethod_00271_amhandler;
CREATE TABLE dropaccessmethod_00271_t (c integer);
CREATE INDEX dropaccessmethod_00271_idx ON dropaccessmethod_00271_t USING dropaccessmethod_00271_schema.dropaccessmethod_00271_am (c);
-- 3. 执行唯一获得覆盖信用的 DROP ACCESS METHOD。
-- primary-target-begin
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00271_schema.dropaccessmethod_00271_am CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS access_method_absent FROM pg_catalog.pg_am WHERE amname = 'dropaccessmethod_00271_am' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00271_schema.dropaccessmethod_00271_am CASCADE;
DROP FUNCTION IF EXISTS dropaccessmethod_00271_amhandler;
DROP SCHEMA IF EXISTS dropaccessmethod_00271_schema CASCADE;
DROP TABLE IF EXISTS dropaccessmethod_00271_t CASCADE;

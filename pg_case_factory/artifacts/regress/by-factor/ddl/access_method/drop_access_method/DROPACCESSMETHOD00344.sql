-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP ACCESS METHOD dependency_state=has_dependent_opclass
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPACCESSMETHOD00344
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/drop_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/drop_access_method.yaml
-- primary_obligation_id: DAM-EXT|00344|drop_access_method|pg_am_catalog_query|DROP_ACCESS_METHOD_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropaccessmethod_00344_t CASCADE;
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00344_schema.dropaccessmethod_00344_am CASCADE;
DROP FUNCTION IF EXISTS dropaccessmethod_00344_amhandler;
DROP SCHEMA IF EXISTS dropaccessmethod_00344_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地访问方法和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropaccessmethod_00344_schema;
CREATE FUNCTION dropaccessmethod_00344_amhandler(internal) RETURNS table_am_handler AS 'MODULE_PATHNAME' LANGUAGE C;
CREATE ACCESS METHOD dropaccessmethod_00344_schema.dropaccessmethod_00344_am TYPE TABLE HANDLER dropaccessmethod_00344_amhandler;
CREATE TABLE dropaccessmethod_00344_t (c integer);
CREATE OPERATOR CLASS dropaccessmethod_00344_opc DEFAULT FOR TYPE integer USING dropaccessmethod_00344_schema.dropaccessmethod_00344_am AS STORAGE integer;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ACCESS METHOD。
-- primary-target-begin
DROP ACCESS METHOD dropaccessmethod_00344_schema.dropaccessmethod_00344_am RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS access_method_present FROM pg_catalog.pg_am WHERE amname = 'dropaccessmethod_00344_am' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP ACCESS METHOD IF EXISTS dropaccessmethod_00344_schema.dropaccessmethod_00344_am CASCADE;
DROP FUNCTION IF EXISTS dropaccessmethod_00344_amhandler;
DROP SCHEMA IF EXISTS dropaccessmethod_00344_schema CASCADE;
DROP TABLE IF EXISTS dropaccessmethod_00344_t CASCADE;

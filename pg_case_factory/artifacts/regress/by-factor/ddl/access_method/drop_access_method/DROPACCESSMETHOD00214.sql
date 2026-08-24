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
-- case_id: DROPACCESSMETHOD00214
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/drop_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/drop_access_method.yaml
-- primary_obligation_id: DAM-EXT|00214|drop_access_method|pg_am_removed_assertion|DROP_ACCESS_METHOD_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ACCESS METHOD IF EXISTS "dropaccessmethod_00214_Quoted" CASCADE;
DROP FUNCTION IF EXISTS dropaccessmethod_00214_amhandler;
DROP ROLE IF EXISTS dropaccessmethod_00214_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地访问方法和因子专用夹具。
CREATE ROLE dropaccessmethod_00214_actor LOGIN NOSUPERUSER;
CREATE FUNCTION dropaccessmethod_00214_amhandler(internal) RETURNS table_am_handler AS 'MODULE_PATHNAME' LANGUAGE C;
CREATE ACCESS METHOD "dropaccessmethod_00214_Quoted" TYPE TABLE HANDLER dropaccessmethod_00214_amhandler;
SET ROLE dropaccessmethod_00214_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ACCESS METHOD。
-- primary-target-begin
DROP ACCESS METHOD IF EXISTS "dropaccessmethod_00214_Quoted";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS access_method_present FROM pg_catalog.pg_am WHERE amname = 'dropaccessmethod_00214_Quoted' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ACCESS METHOD IF EXISTS "dropaccessmethod_00214_Quoted" CASCADE;
DROP FUNCTION IF EXISTS dropaccessmethod_00214_amhandler;
DROP OWNED BY dropaccessmethod_00214_actor;
DROP ROLE IF EXISTS dropaccessmethod_00214_actor;

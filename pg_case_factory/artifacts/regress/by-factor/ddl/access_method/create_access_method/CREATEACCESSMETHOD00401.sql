-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ACCESS METHOD privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEACCESSMETHOD00401
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/create_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/create_access_method.yaml
-- primary_obligation_id: CAM-EXT|00401|pg_am_handler_check|DROP_ACCESS_METHOD
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ACCESS METHOD IF EXISTS "createaccessmethod_00401_select";
DROP FUNCTION IF EXISTS "createaccessmethod_00401_Mixed Handler"(internal);
DROP OWNED BY createaccessmethod_00401_actor CASCADE;
DROP ROLE IF EXISTS createaccessmethod_00401_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createaccessmethod_00401_actor LOGIN NOSUPERUSER;
CREATE FUNCTION "createaccessmethod_00401_Mixed Handler"(internal) RETURNS internal AS 'MODULE_PATHNAME', 'cam_handler' LANGUAGE C;
SET ROLE createaccessmethod_00401_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE ACCESS METHOD。
-- primary-target-begin
CREATE ACCESS METHOD "createaccessmethod_00401_select" TYPE INDEX HANDLER "createaccessmethod_00401_Mixed Handler";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS handler_state FROM pg_catalog.pg_proc WHERE proname = 'createaccessmethod_00401_Mixed Handler' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ACCESS METHOD IF EXISTS "createaccessmethod_00401_select";
DROP FUNCTION IF EXISTS "createaccessmethod_00401_Mixed Handler"(internal);
DROP OWNED BY createaccessmethod_00401_actor CASCADE;
DROP ROLE IF EXISTS createaccessmethod_00401_actor;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ACCESS METHOD handler_function_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEACCESSMETHOD00294
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/create_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/create_access_method.yaml
-- primary_obligation_id: CAM-EXT|00294|pg_am_handler_check|DROP_ACCESS_METHOD_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ACCESS METHOD IF EXISTS "createaccessmethod_00294_Mixed Am";
DROP FUNCTION IF EXISTS "createaccessmethod_00294_Mixed Handler"(internal);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE ACCESS METHOD。
-- primary-target-begin
CREATE ACCESS METHOD "createaccessmethod_00294_Mixed Am" TYPE INDEX HANDLER "createaccessmethod_00294_Mixed Handler";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS handler_state FROM pg_catalog.pg_proc WHERE proname = 'createaccessmethod_00294_Mixed Handler' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP ACCESS METHOD IF EXISTS "createaccessmethod_00294_Mixed Am";
DROP FUNCTION IF EXISTS "createaccessmethod_00294_Mixed Handler"(internal);

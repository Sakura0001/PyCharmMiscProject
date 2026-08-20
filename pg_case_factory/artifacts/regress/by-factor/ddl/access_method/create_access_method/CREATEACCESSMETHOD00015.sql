-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ACCESS METHOD handler_dependency=handler_exists_wrong_return_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEACCESSMETHOD00015
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/create_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/create_access_method.yaml
-- primary_obligation_id: CAM-SFV|sfv-b77a9d9f6ea74cb8c3d7589f|create_access_method
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ACCESS METHOD IF EXISTS createaccessmethod_00015_am;
DROP FUNCTION IF EXISTS createaccessmethod_00015_handler(internal);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaccessmethod_00015_handler(internal) RETURNS text AS 'MODULE_PATHNAME', 'cam_handler' LANGUAGE C;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE ACCESS METHOD。
-- primary-target-begin
CREATE ACCESS METHOD createaccessmethod_00015_am TYPE INDEX HANDLER createaccessmethod_00015_handler;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS am_state FROM pg_catalog.pg_am WHERE amname = 'createaccessmethod_00015_am' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP ACCESS METHOD IF EXISTS createaccessmethod_00015_am;
DROP FUNCTION IF EXISTS createaccessmethod_00015_handler(internal);

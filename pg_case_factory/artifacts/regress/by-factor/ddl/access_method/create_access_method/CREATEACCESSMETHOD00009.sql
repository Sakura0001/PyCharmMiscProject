-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ACCESS METHOD cleanup_mode=DROP_ACCESS_METHOD_IF_EXISTS
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEACCESSMETHOD00009
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/create_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/create_access_method.yaml
-- primary_obligation_id: CAM-SFV|sfv-60dd76b88fd69d4b7329e1ee|create_access_method
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ACCESS METHOD IF EXISTS createaccessmethod_00009_am;
DROP FUNCTION IF EXISTS createaccessmethod_00009_handler(internal);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaccessmethod_00009_handler(internal) RETURNS internal AS 'MODULE_PATHNAME', 'cam_handler' LANGUAGE C;
-- 3. 执行唯一获得覆盖信用的 CREATE ACCESS METHOD。
-- primary-target-begin
CREATE ACCESS METHOD createaccessmethod_00009_am TYPE INDEX HANDLER createaccessmethod_00009_handler;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS am_state FROM pg_catalog.pg_am WHERE amname = 'createaccessmethod_00009_am' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP ACCESS METHOD IF EXISTS createaccessmethod_00009_am;
DROP FUNCTION IF EXISTS createaccessmethod_00009_handler(internal);

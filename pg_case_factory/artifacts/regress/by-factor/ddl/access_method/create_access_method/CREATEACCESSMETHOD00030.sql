-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ACCESS METHOD verification_mode=pg_am_actual_usage
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEACCESSMETHOD00030
-- source_md: skills/pg-sql-generation/references/statements/ddl/access_method/create_access_method.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/access_method/create_access_method.yaml
-- primary_obligation_id: CAM-SFV|sfv-f945983038652cd8c56172e3|create_access_method
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createaccessmethod_00030_fixture;
DROP ACCESS METHOD IF EXISTS createaccessmethod_00030_am;
DROP FUNCTION IF EXISTS createaccessmethod_00030_handler(internal);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaccessmethod_00030_handler(internal) RETURNS internal AS 'MODULE_PATHNAME', 'cam_handler' LANGUAGE C;
-- 3. 执行唯一获得覆盖信用的 CREATE ACCESS METHOD。
-- primary-target-begin
CREATE ACCESS METHOD createaccessmethod_00030_am TYPE INDEX HANDLER createaccessmethod_00030_handler;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
CREATE TABLE createaccessmethod_00030_fixture (id integer);
CREATE INDEX createaccessmethod_00030_idx ON createaccessmethod_00030_fixture USING createaccessmethod_00030_am;
SELECT count(*) > 0 AS am_usage FROM pg_catalog.pg_class WHERE relname = 'createaccessmethod_00030_idx' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP ACCESS METHOD IF EXISTS createaccessmethod_00030_am;
DROP FUNCTION IF EXISTS createaccessmethod_00030_handler(internal);
DROP TABLE IF EXISTS createaccessmethod_00030_fixture;

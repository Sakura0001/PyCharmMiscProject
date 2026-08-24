-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP VIEW privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPVIEW02847
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/drop_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/drop_view.yaml
-- primary_obligation_id: DROPVIEW-EXT|02847|drop_view|notice_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropview_02847_vbt CASCADE;
DROP VIEW IF EXISTS dropview_02847_noexist CASCADE;
DROP POLICY IF EXISTS dropview_02847_pol ON dropview_02847_noexist;
DROP OWNED BY dropview_02847_actor;
DROP ROLE IF EXISTS dropview_02847_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE dropview_02847_actor LOGIN NOSUPERUSER;
CREATE TABLE dropview_02847_vbt (c integer);
SET ROLE dropview_02847_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP VIEW。
-- primary-target-begin
DROP VIEW IF EXISTS dropview_02847_noexist RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS view_absent FROM pg_catalog.pg_class WHERE relname = 'dropview_02847_noexist' AND relkind = 'v' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS dropview_02847_noexist CASCADE;
DROP POLICY IF EXISTS dropview_02847_pol ON dropview_02847_noexist;
DROP OWNED BY dropview_02847_actor;
DROP ROLE IF EXISTS dropview_02847_actor;
DROP TABLE IF EXISTS dropview_02847_vbt CASCADE;

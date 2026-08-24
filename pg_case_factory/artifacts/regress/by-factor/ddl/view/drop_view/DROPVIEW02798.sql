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
-- case_id: DROPVIEW02798
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/drop_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/drop_view.yaml
-- primary_obligation_id: DROPVIEW-EXT|02798|drop_view|notice_assertion|manual_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropview_02798_vbt CASCADE;
DROP VIEW IF EXISTS "dropview_02798_qv" CASCADE;
DROP POLICY IF EXISTS dropview_02798_pol ON "dropview_02798_qv";
DROP OWNED BY dropview_02798_actor;
DROP ROLE IF EXISTS dropview_02798_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE dropview_02798_actor LOGIN NOSUPERUSER;
CREATE TABLE dropview_02798_vbt (c integer);
CREATE VIEW "dropview_02798_qv" AS SELECT * FROM dropview_02798_vbt;
ALTER TABLE "dropview_02798_qv" ENABLE ROW LEVEL SECURITY;
CREATE POLICY dropview_02798_pol ON "dropview_02798_qv" USING (true);
SET ROLE dropview_02798_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP VIEW。
-- primary-target-begin
DROP VIEW IF EXISTS "dropview_02798_qv" RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_present FROM pg_catalog.pg_class WHERE relname = 'dropview_02798_qv' AND relkind = 'v' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS "dropview_02798_qv" CASCADE;
DROP POLICY IF EXISTS dropview_02798_pol ON "dropview_02798_qv";
DROP OWNED BY dropview_02798_actor;
DROP ROLE IF EXISTS dropview_02798_actor;
DROP TABLE IF EXISTS dropview_02798_vbt CASCADE;

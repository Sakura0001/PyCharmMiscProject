-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER MATERIALIZED VIEW statement_branch=branch_set_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERMATERIALIZEDVIEW00052
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-SFV|sfv-4c8e445858f56e2e1267e456|set_schema
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_00052_mv;
DROP ROLE IF EXISTS altermaterializedview_00052_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE ROLE altermaterializedview_00052_new_owner LOGIN;
CREATE MATERIALIZED VIEW altermaterializedview_00052_mv AS SELECT 1 AS altermaterializedview_00052_col;
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW altermaterializedview_00052_mv SET SCHEMA public;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mview_present FROM pg_catalog.pg_class WHERE relname = 'altermaterializedview_00052_mv' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_00052_mv;
DROP OWNED BY altermaterializedview_00052_new_owner CASCADE;
DROP ROLE IF EXISTS altermaterializedview_00052_new_owner;

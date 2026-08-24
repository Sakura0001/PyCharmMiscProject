-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER MATERIALIZED VIEW privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERMATERIALIZEDVIEW08353
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-EXT|08353|set_without_cluster|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_08353_mv;
DROP ROLE IF EXISTS altermaterializedview_08353_actor;
DROP ROLE IF EXISTS altermaterializedview_08353_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE ROLE altermaterializedview_08353_new_owner LOGIN;
CREATE ROLE altermaterializedview_08353_actor LOGIN NOSUPERUSER;
CREATE MATERIALIZED VIEW altermaterializedview_08353_mv AS SELECT 1 AS altermaterializedview_08353_col;
SET ROLE altermaterializedview_08353_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW IF EXISTS public.altermaterializedview_08353_mv SET WITHOUT CLUSTER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_08353_mv;
DROP OWNED BY altermaterializedview_08353_actor;
DROP ROLE IF EXISTS altermaterializedview_08353_actor;
DROP OWNED BY altermaterializedview_08353_new_owner;
DROP ROLE IF EXISTS altermaterializedview_08353_new_owner;

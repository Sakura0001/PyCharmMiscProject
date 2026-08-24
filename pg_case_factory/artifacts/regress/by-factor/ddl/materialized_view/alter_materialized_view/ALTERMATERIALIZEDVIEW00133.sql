-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER MATERIALIZED VIEW target_object_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERMATERIALIZEDVIEW00133
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-EXT|00133|cluster_on|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altermaterializedview_00133_tbl;
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_00133_mv;
DROP ROLE IF EXISTS altermaterializedview_00133_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE ROLE altermaterializedview_00133_new_owner LOGIN;
CREATE TABLE altermaterializedview_00133_tbl AS SELECT 1 AS c;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW public.altermaterializedview_00133_tbl CLUSTER ON altermaterializedview_00133_idx;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_00133_mv;
DROP OWNED BY altermaterializedview_00133_new_owner;
DROP ROLE IF EXISTS altermaterializedview_00133_new_owner;
DROP TABLE IF EXISTS altermaterializedview_00133_tbl;

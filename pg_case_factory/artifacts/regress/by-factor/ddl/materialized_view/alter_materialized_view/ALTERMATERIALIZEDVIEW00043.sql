-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER MATERIALIZED VIEW ownership_boundary=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERMATERIALIZEDVIEW00043
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-SFV|sfv-c8dca99e925b51819199e3bd|set_statistics
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_00043_mv;
DROP ROLE IF EXISTS altermaterializedview_00043_actor;
DROP ROLE IF EXISTS altermaterializedview_00043_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE ROLE altermaterializedview_00043_new_owner LOGIN;
CREATE ROLE altermaterializedview_00043_actor LOGIN NOSUPERUSER;
CREATE MATERIALIZED VIEW altermaterializedview_00043_mv AS SELECT 1 AS altermaterializedview_00043_col;
SET ROLE altermaterializedview_00043_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW altermaterializedview_00043_mv ALTER COLUMN altermaterializedview_00043_col SET STATISTICS 100;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mview_present FROM pg_catalog.pg_class WHERE relname = 'altermaterializedview_00043_mv' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_00043_mv;
DROP OWNED BY altermaterializedview_00043_actor CASCADE;
DROP ROLE IF EXISTS altermaterializedview_00043_actor;
DROP OWNED BY altermaterializedview_00043_new_owner CASCADE;
DROP ROLE IF EXISTS altermaterializedview_00043_new_owner;

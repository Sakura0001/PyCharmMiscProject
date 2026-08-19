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
-- case_id: ALTERMATERIALIZEDVIEW08078
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-EXT|08078|set_without_cluster|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_08078_mv;
DROP ROLE IF EXISTS altermaterializedview_08078_actor;
DROP ROLE IF EXISTS altermaterializedview_08078_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE ROLE altermaterializedview_08078_new_owner LOGIN;
CREATE ROLE altermaterializedview_08078_actor LOGIN NOSUPERUSER;
CREATE MATERIALIZED VIEW altermaterializedview_08078_mv AS SELECT 1 AS altermaterializedview_08078_col;
SET ROLE altermaterializedview_08078_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW IF EXISTS public.altermaterializedview_08078_mv SET WITHOUT CLUSTER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mview_present FROM pg_catalog.pg_class WHERE relname = 'altermaterializedview_08078_mv' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_08078_mv;
DROP OWNED BY altermaterializedview_08078_actor CASCADE;
DROP ROLE IF EXISTS altermaterializedview_08078_actor;
DROP OWNED BY altermaterializedview_08078_new_owner CASCADE;
DROP ROLE IF EXISTS altermaterializedview_08078_new_owner;

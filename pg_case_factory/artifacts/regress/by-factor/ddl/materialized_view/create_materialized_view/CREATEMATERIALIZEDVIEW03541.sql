-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE MATERIALIZED VIEW privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEMATERIALIZEDVIEW03541
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/create_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/create_materialized_view.yaml
-- primary_obligation_id: CMATVIEW-EXT|03541|returned_rows|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS public.creatematerializedview_03541_mv;
DROP OWNED BY creatematerializedview_03541_actor CASCADE;
DROP ROLE IF EXISTS creatematerializedview_03541_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE creatematerializedview_03541_actor LOGIN NOSUPERUSER;
SET ROLE creatematerializedview_03541_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE MATERIALIZED VIEW。
-- primary-target-begin
CREATE MATERIALIZED VIEW public.creatematerializedview_03541_mv AS WITH creatematerializedview_03541_cte AS (SELECT 1 AS c1, 2 AS c2) SELECT c1, c2 FROM creatematerializedview_03541_cte WITH DATA;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = AS returned_rows_absent FROM pg_catalog.pg_matviews WHERE matviewname = 'creatematerializedview_03541_mv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP MATERIALIZED VIEW IF EXISTS public.creatematerializedview_03541_mv;
DROP OWNED BY creatematerializedview_03541_actor CASCADE;
DROP ROLE IF EXISTS creatematerializedview_03541_actor;

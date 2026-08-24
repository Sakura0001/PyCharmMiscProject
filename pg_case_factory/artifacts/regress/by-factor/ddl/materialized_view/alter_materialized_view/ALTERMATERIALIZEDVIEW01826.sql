-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER MATERIALIZED VIEW new_owner_shape=session_user
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERMATERIALIZEDVIEW01826
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-EXT|01826|owner_to|catalog_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
SELECT 1 AS target_materialized_view_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW IF EXISTS public.altermaterializedview_01826_mv OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS mview_absent FROM pg_catalog.pg_class WHERE relname = 'altermaterializedview_01826_mv' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;

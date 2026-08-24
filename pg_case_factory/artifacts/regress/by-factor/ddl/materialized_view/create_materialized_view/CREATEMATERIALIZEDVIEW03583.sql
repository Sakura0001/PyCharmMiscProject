-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE MATERIALIZED VIEW query_source_state=source_table_missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEMATERIALIZEDVIEW03583
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/create_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/create_materialized_view.yaml
-- primary_obligation_id: CMATVIEW-EXT|03583|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS public.creatematerializedview_03583_mv;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE MATERIALIZED VIEW。
-- primary-target-begin
CREATE MATERIALIZED VIEW public.creatematerializedview_03583_mv AS SELECT * FROM creatematerializedview_03583_nosrc WITH DATA;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS public.creatematerializedview_03583_mv;

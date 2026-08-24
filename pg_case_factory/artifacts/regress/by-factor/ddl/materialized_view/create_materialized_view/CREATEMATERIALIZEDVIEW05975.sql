-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE MATERIALIZED VIEW target_action=create_matview
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEMATERIALIZEDVIEW05975
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/create_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/create_materialized_view.yaml
-- primary_obligation_id: CMATVIEW-EXT|05975|error_assertion|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS creatematerializedview_05975_mv;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
-- 3. 执行唯一获得覆盖信用的 CREATE MATERIALIZED VIEW。
-- primary-target-begin
CREATE MATERIALIZED VIEW IF NOT EXISTS creatematerializedview_05975_mv AS SELECT 1::int AS c1, 'x'::text AS c2 WITH NO DATA;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS creatematerializedview_05975_mv;

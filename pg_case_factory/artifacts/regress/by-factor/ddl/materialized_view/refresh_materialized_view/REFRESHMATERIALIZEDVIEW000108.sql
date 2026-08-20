-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : REFRESH MATERIALIZED VIEW target_object_state=missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REFRESHMATERIALIZEDVIEW000108
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/refresh_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/refresh_materialized_view.yaml
-- primary_obligation_id: REFRESHMATERIALIZEDVIEW-EXT|000108|returned_rows|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS refreshmaterializedview_000108_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE refreshmaterializedview_000108_actor LOGIN NOSUPERUSER;
SET ROLE refreshmaterializedview_000108_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REFRESH MATERIALIZED VIEW。
-- primary-target-begin
REFRESH MATERIALIZED VIEW refreshmaterializedview_000108_no_such_mv WITH DATA;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) AS returned_row_count FROM refreshmaterializedview_000108_mv ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY refreshmaterializedview_000108_actor;
DROP ROLE IF EXISTS refreshmaterializedview_000108_actor;

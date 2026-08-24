-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : REFRESH MATERIALIZED VIEW privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REFRESHMATERIALIZEDVIEW000778
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/refresh_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/refresh_materialized_view.yaml
-- primary_obligation_id: REFRESHMATERIALIZEDVIEW-EXT|000778|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS refreshmaterializedview_000778_src CASCADE;
DROP MATERIALIZED VIEW IF EXISTS refreshmaterializedview_000778_mv;
DROP ROLE IF EXISTS refreshmaterializedview_000778_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE refreshmaterializedview_000778_actor LOGIN NOSUPERUSER;
CREATE TABLE refreshmaterializedview_000778_src (id integer);
INSERT INTO refreshmaterializedview_000778_src VALUES (1), (2), (3);
CREATE MATERIALIZED VIEW refreshmaterializedview_000778_mv AS SELECT id FROM refreshmaterializedview_000778_src;
CREATE UNIQUE INDEX refreshmaterializedview_000778_uidx ON refreshmaterializedview_000778_mv (id);
SET ROLE refreshmaterializedview_000778_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REFRESH MATERIALIZED VIEW。
-- primary-target-begin
REFRESH MATERIALIZED VIEW refreshmaterializedview_000778_sch.refreshmaterializedview_000778_mv WITH NO DATA;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS refreshed_row_count FROM refreshmaterializedview_000778_mv ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY refreshmaterializedview_000778_actor;
DROP ROLE IF EXISTS refreshmaterializedview_000778_actor;
DROP MATERIALIZED VIEW IF EXISTS refreshmaterializedview_000778_mv;
DROP TABLE IF EXISTS refreshmaterializedview_000778_src CASCADE;

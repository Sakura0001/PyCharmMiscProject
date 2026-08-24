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
-- case_id: ALTERMATERIALIZEDVIEW02408
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-EXT|02408|owner_to|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altermaterializedview_02408_tbl;
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_02408_mv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE TABLE altermaterializedview_02408_tbl AS SELECT 1 AS c;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW IF EXISTS "altermaterializedview_02408_tbl" OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS mview_absent FROM pg_catalog.pg_class WHERE relname = 'altermaterializedview_02408_tbl' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_02408_mv;
DROP TABLE IF EXISTS altermaterializedview_02408_tbl;

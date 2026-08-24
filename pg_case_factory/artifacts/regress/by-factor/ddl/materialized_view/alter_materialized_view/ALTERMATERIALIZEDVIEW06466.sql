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
-- case_id: ALTERMATERIALIZEDVIEW06466
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/alter_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/alter_materialized_view.yaml
-- primary_obligation_id: AMV-EXT|06466|set_storage|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altermaterializedview_06466_tbl;
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_06466_mv;
DROP ROLE IF EXISTS altermaterializedview_06466_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE ROLE altermaterializedview_06466_new_owner LOGIN;
CREATE TABLE altermaterializedview_06466_tbl AS SELECT 1 AS c;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。
-- primary-target-begin
ALTER MATERIALIZED VIEW IF EXISTS public.altermaterializedview_06466_tbl ALTER COLUMN altermaterializedview_06466_col SET STORAGE PLAIN;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_not_verified FROM pg_catalog.pg_class WHERE relname = 'altermaterializedview_06466_tbl' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS altermaterializedview_06466_mv;
DROP OWNED BY altermaterializedview_06466_new_owner CASCADE;
DROP ROLE IF EXISTS altermaterializedview_06466_new_owner;
DROP TABLE IF EXISTS altermaterializedview_06466_tbl;

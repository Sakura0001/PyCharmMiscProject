-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FOREIGN TABLE dependency_state=has_view_dependency
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFOREIGNTABLE00325
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/drop_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/drop_foreign_table.yaml
-- primary_obligation_id: DROPFOREIGNTABLE-EXT|00325|drop_foreign_table|error_assertion|drop_dependent_views
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS dropforeigntable_00325_v;
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00325_ft;
DROP SERVER IF EXISTS dropforeigntable_00325_server;
\set ON_ERROR_STOP on
-- 2. 创建完整本地外部表和因子专用夹具。
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER dropforeigntable_00325_server FOREIGN DATA WRAPPER file_fdw;
CREATE FOREIGN TABLE dropforeigntable_00325_ft (c integer) SERVER dropforeigntable_00325_server;
CREATE VIEW dropforeigntable_00325_v AS SELECT * FROM dropforeigntable_00325_ft;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN TABLE。
-- primary-target-begin
DROP FOREIGN TABLE dropforeigntable_00325_ft;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS foreign_table_present FROM pg_catalog.pg_class WHERE relname = 'dropforeigntable_00325_ft' AND relkind = 'f' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS dropforeigntable_00325_v;
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00325_ft;
DROP SERVER IF EXISTS dropforeigntable_00325_server;

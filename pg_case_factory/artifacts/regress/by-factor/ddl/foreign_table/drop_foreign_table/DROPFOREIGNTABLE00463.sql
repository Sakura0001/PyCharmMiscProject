-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FOREIGN TABLE object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFOREIGNTABLE00463
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/drop_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/drop_foreign_table.yaml
-- primary_obligation_id: DROPFOREIGNTABLE-EXT|00463|drop_foreign_table|notice_assertion|recreate_foreign_table
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00463_ft;
DROP SERVER IF EXISTS dropforeigntable_00463_server;
\set ON_ERROR_STOP on
-- 2. 创建完整本地外部表和因子专用夹具。
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER dropforeigntable_00463_server FOREIGN DATA WRAPPER file_fdw;
CREATE FOREIGN TABLE dropforeigntable_00463_ft (c integer) SERVER dropforeigntable_00463_server;
-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN TABLE。
-- primary-target-begin
DROP FOREIGN TABLE dropforeigntable_00463_ft;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS foreign_table_absent FROM pg_catalog.pg_class WHERE relname = 'dropforeigntable_00463_ft' AND relkind = 'f' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00463_ft;
DROP SERVER IF EXISTS dropforeigntable_00463_server;

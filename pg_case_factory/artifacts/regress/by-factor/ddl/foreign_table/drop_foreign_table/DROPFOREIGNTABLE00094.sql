-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FOREIGN TABLE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFOREIGNTABLE00094
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/drop_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/drop_foreign_table.yaml
-- primary_obligation_id: DROPFOREIGNTABLE-EXT|00094|drop_foreign_table|pg_class_catalog_query|recreate_fdw
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS dropforeigntable_00094_v;
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00094_ft;
DROP SERVER IF EXISTS dropforeigntable_00094_server;
DROP OWNED BY dropforeigntable_00094_actor;
DROP ROLE IF EXISTS dropforeigntable_00094_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地外部表和因子专用夹具。
CREATE ROLE dropforeigntable_00094_actor LOGIN NOSUPERUSER;
SELECT 1 AS target_foreign_table_intentionally_absent;
SET ROLE dropforeigntable_00094_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN TABLE。
-- primary-target-begin
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00094_ft CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS foreign_table_absent FROM pg_catalog.pg_class WHERE relname = 'dropforeigntable_00094_ft' AND relkind = 'f' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS dropforeigntable_00094_v;
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00094_ft;
DROP SERVER IF EXISTS dropforeigntable_00094_server;
DROP OWNED BY dropforeigntable_00094_actor;
DROP ROLE IF EXISTS dropforeigntable_00094_actor;

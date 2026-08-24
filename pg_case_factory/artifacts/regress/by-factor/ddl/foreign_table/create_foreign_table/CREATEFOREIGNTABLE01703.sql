-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN TABLE privilege_level=no_server_usage
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNTABLE01703
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/create_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/create_foreign_table.yaml
-- primary_obligation_id: CFT-EXT|01703|pg_class_catalog_query|drop_foreign_table_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS createforeigntable_01703_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_01703_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_01703_fdw CASCADE;
DROP OWNED BY createforeigntable_01703_actor CASCADE;
DROP ROLE IF EXISTS createforeigntable_01703_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE FOREIGN DATA WRAPPER createforeigntable_01703_fdw;
CREATE SERVER createforeigntable_01703_server FOREIGN DATA WRAPPER createforeigntable_01703_fdw;
CREATE ROLE createforeigntable_01703_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN DATA WRAPPER createforeigntable_01703_fdw TO createforeigntable_01703_actor;
GRANT USAGE ON FOREIGN SERVER createforeigntable_01703_server TO createforeigntable_01703_actor;
SET ROLE createforeigntable_01703_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。
-- primary-target-begin
CREATE FOREIGN TABLE createforeigntable_01703_ft (createforeigntable_01703_col numeric(10,2)) SERVER createforeigntable_01703_server;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS ft_state FROM pg_catalog.pg_class WHERE relname = 'createforeigntable_01703_ft' AND relkind = 'f' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS createforeigntable_01703_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_01703_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_01703_fdw CASCADE;
DROP OWNED BY createforeigntable_01703_actor CASCADE;
DROP ROLE IF EXISTS createforeigntable_01703_actor;

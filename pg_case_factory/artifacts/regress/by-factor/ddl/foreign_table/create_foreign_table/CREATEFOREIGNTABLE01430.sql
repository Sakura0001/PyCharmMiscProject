-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN TABLE object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNTABLE01430
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/create_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/create_foreign_table.yaml
-- primary_obligation_id: CFT-EXT|01430|notice_assertion|drop_fdw
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS createforeigntable_01430_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_01430_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_01430_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE FOREIGN DATA WRAPPER createforeigntable_01430_fdw;
CREATE SERVER createforeigntable_01430_server FOREIGN DATA WRAPPER createforeigntable_01430_fdw;
CREATE FOREIGN TABLE createforeigntable_01430_ft () SERVER createforeigntable_01430_server;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。
-- primary-target-begin
CREATE FOREIGN TABLE createforeigntable_01430_ft (createforeigntable_01430_col integer) SERVER createforeigntable_01430_server;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS ft_state FROM pg_catalog.pg_class WHERE relname = 'createforeigntable_01430_ft' AND relkind = 'f' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS createforeigntable_01430_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_01430_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_01430_fdw CASCADE;

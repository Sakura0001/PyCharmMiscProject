-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN TABLE column_data_type=numeric
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNTABLE00022
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/create_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/create_foreign_table.yaml
-- primary_obligation_id: CFT-SFV|sfv-b18d0ce4ddd1737ee534382b|create_regular
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS createforeigntable_00022_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_00022_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_00022_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE FOREIGN DATA WRAPPER createforeigntable_00022_fdw;
CREATE SERVER createforeigntable_00022_server FOREIGN DATA WRAPPER createforeigntable_00022_fdw;
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。
-- primary-target-begin
CREATE FOREIGN TABLE createforeigntable_00022_ft (createforeigntable_00022_col numeric(10,2)) SERVER createforeigntable_00022_server;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS ft_state FROM pg_catalog.pg_class WHERE relname = 'createforeigntable_00022_ft' AND relkind = 'f' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS createforeigntable_00022_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_00022_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_00022_fdw CASCADE;

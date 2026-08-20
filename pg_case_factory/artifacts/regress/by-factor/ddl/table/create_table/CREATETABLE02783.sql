-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLE table_type=temporary_local
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLE02783
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/create_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/create_table.yaml
-- primary_obligation_id: CT-EXT|02783|SELECT_count|DROP_TABLE_CASCADE|main
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtable_02783_t, createtable_02783_reftab CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createtable_02783_reftab (createtable_02783_col integer PRIMARY KEY);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TABLE。
-- primary-target-begin
CREATE LOCAL TEMPORARY TABLE createtable_02783_t (createtable_02783_col integer, FOREIGN KEY (createtable_02783_col) REFERENCES createtable_02783_reftab(createtable_02783_col)) PARTITION BY LIST (createtable_02783_col);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS exists_check FROM pg_catalog.pg_class WHERE relname = 'createtable_02783_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS createtable_02783_t, createtable_02783_reftab CASCADE;

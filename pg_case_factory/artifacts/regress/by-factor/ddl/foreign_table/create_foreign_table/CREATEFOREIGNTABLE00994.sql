-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN TABLE server_existence=server_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNTABLE00994
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/create_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/create_foreign_table.yaml
-- primary_obligation_id: CFT-EXT|00994|notice_assertion|drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS createforeigntable_00994_ft CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。
-- primary-target-begin
CREATE FOREIGN TABLE createforeigntable_00994_ft (createforeigntable_00994_col integer GENERATED ALWAYS AS (1) VIRTUAL NOT ENFORCED) SERVER createforeigntable_00994_noserver;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS ft_state FROM pg_catalog.pg_class WHERE relname = 'createforeigntable_00994_ft' AND relkind = 'f' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS createforeigntable_00994_ft CASCADE;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : VACUUM resource_boundary=missing_file_or_library
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: VACUUM00031
-- source_md: skills/pg-sql-generation/references/statements/utility/maintenance/vacuum.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/maintenance/vacuum.yaml
-- primary_obligation_id: VACUUM-SFV|sfv-03e25a6148f2bcaa8c6a63f1|vacuum_resource_boundary
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS vacuum_00031_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE vacuum_00031_t (id integer);
INSERT INTO vacuum_00031_t (id) VALUES (1), (2);
-- 3. 执行唯一获得覆盖信用的 VACUUM。
-- primary-target-begin
VACUUM vacuum_00031_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS catalog_relation_count FROM pg_catalog.pg_class c WHERE c.relname = 'vacuum_00031_t' AND c.relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS vacuum_00031_t CASCADE;

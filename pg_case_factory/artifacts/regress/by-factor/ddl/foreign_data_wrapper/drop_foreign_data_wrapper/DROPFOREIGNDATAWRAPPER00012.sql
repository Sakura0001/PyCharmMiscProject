-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FOREIGN DATA WRAPPER dependent_with_restrict=has_deps_restrict
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFOREIGNDATAWRAPPER00012
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_data_wrapper/drop_foreign_data_wrapper.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_data_wrapper/drop_foreign_data_wrapper.yaml
-- primary_obligation_id: DROPFOREIGNDATAWRAPPER-SFV|sfv-3d3ab50e058b24add153a16d|drop_foreign_data_wrapper
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN DATA WRAPPER IF EXISTS dropforeigndatawrapper_00012_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地FDW和因子专用夹具。
CREATE FOREIGN DATA WRAPPER dropforeigndatawrapper_00012_fdw;
-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN DATA WRAPPER。
-- primary-target-begin
DROP FOREIGN DATA WRAPPER dropforeigndatawrapper_00012_fdw;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS fdw_absent FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname = 'dropforeigndatawrapper_00012_fdw' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP FOREIGN DATA WRAPPER IF EXISTS dropforeigndatawrapper_00012_fdw CASCADE;

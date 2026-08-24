-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FOREIGN DATA WRAPPER privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFOREIGNDATAWRAPPER00377
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_data_wrapper/drop_foreign_data_wrapper.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_data_wrapper/drop_foreign_data_wrapper.yaml
-- primary_obligation_id: DROPFOREIGNDATAWRAPPER-EXT|00377|drop_foreign_data_wrapper|notice_assertion|recreate_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS dropforeigndatawrapper_00377_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropforeigndatawrapper_00377_fdw CASCADE;
DROP OWNED BY dropforeigndatawrapper_00377_actor;
DROP ROLE IF EXISTS dropforeigndatawrapper_00377_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地FDW和因子专用夹具。
CREATE ROLE dropforeigndatawrapper_00377_actor LOGIN NOSUPERUSER;
CREATE FOREIGN DATA WRAPPER dropforeigndatawrapper_00377_fdw;
CREATE SERVER dropforeigndatawrapper_00377_server FOREIGN DATA WRAPPER dropforeigndatawrapper_00377_fdw;
SET ROLE dropforeigndatawrapper_00377_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN DATA WRAPPER。
-- primary-target-begin
DROP FOREIGN DATA WRAPPER IF EXISTS dropforeigndatawrapper_00377_fdw CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS fdw_present FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname = 'dropforeigndatawrapper_00377_fdw' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS dropforeigndatawrapper_00377_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropforeigndatawrapper_00377_fdw CASCADE;
DROP OWNED BY dropforeigndatawrapper_00377_actor;
DROP ROLE IF EXISTS dropforeigndatawrapper_00377_actor;

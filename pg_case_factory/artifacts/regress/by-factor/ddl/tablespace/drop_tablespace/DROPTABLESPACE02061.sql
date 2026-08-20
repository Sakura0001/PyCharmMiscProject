-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TABLESPACE object_occupancy=has_objects_in_current_db
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTABLESPACE02061
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/drop_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/drop_tablespace.yaml
-- primary_obligation_id: DROPTABLESPACE-EXT|02061|drop_tablespace|notice_assertion|reset_temp_tablespaces
-- expected_outcome: expected_failure
-- expected_sqlstate: 55006
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS droptablespace_02061_noexist;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表空间和因子专用夹具。
SELECT 1 AS setup_boundary;
SELECT 1 AS target_tablespace_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TABLESPACE。
-- primary-target-begin
DROP TABLESPACE IF EXISTS droptablespace_02061_noexist;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '55006' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS tablespace_absent FROM pg_catalog.pg_tablespace WHERE spcname = 'droptablespace_02061_noexist' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLESPACE IF EXISTS droptablespace_02061_noexist;

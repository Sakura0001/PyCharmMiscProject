-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TABLESPACE dependency_context=temp_tablespace_active
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTABLESPACE00226
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/drop_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/drop_tablespace.yaml
-- primary_obligation_id: DROPTABLESPACE-EXT|00226|drop_tablespace|catalog_query|remove_objects_first
-- expected_outcome: expected_failure
-- expected_sqlstate: 55006
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS "droptablespace_00226_qts";
\set ON_ERROR_STOP on
-- 2. 创建完整本地表空间和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLESPACE "droptablespace_00226_qts" LOCATION '/tmp/droptablespace_00226_tsloc';
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TABLESPACE。
-- primary-target-begin
DROP TABLESPACE "droptablespace_00226_qts";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '55006' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS tablespace_present FROM pg_catalog.pg_tablespace WHERE spcname = 'droptablespace_00226_qts' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLESPACE IF EXISTS "droptablespace_00226_qts";

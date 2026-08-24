-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TABLESPACE authorization_path=non_owner_non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTABLESPACE00132
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/drop_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/drop_tablespace.yaml
-- primary_obligation_id: DROPTABLESPACE-EXT|00132|drop_tablespace|error_assertion|reset_temp_tablespaces
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS droptablespace_00132_ts;
DROP OWNED BY droptablespace_00132_actor;
DROP ROLE IF EXISTS droptablespace_00132_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表空间和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droptablespace_00132_actor LOGIN NOSUPERUSER;
CREATE TABLESPACE droptablespace_00132_ts LOCATION '/tmp/droptablespace_00132_tsloc';
SET ROLE droptablespace_00132_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TABLESPACE。
-- primary-target-begin
DROP TABLESPACE IF EXISTS droptablespace_00132_ts;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS tablespace_present FROM pg_catalog.pg_tablespace WHERE spcname = 'droptablespace_00132_ts' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TABLESPACE IF EXISTS droptablespace_00132_ts;
DROP OWNED BY droptablespace_00132_actor;
DROP ROLE IF EXISTS droptablespace_00132_actor;

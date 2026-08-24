-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP STATISTICS executor_privilege=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSTATISTICS00939
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/drop_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/drop_statistics.yaml
-- primary_obligation_id: DROPSTATISTICS-EXT|00939|drop_statistics|error_assertion|drop_statistics
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropstatistics_00939_t CASCADE;
DROP STATISTICS IF EXISTS "dropstatistics_00939_qstat";
DROP STATISTICS IF EXISTS dropstatistics_00939_stat2;
DROP OWNED BY dropstatistics_00939_actor;
DROP ROLE IF EXISTS dropstatistics_00939_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地统计和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE dropstatistics_00939_actor LOGIN NOSUPERUSER;
CREATE TABLE dropstatistics_00939_t (c1 integer, c2 integer);
CREATE STATISTICS "dropstatistics_00939_qstat" ON dropstatistics_00939_t (c1, c2);
CREATE STATISTICS dropstatistics_00939_stat2 ON dropstatistics_00939_t (c1, c2);
SET ROLE dropstatistics_00939_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP STATISTICS。
-- primary-target-begin
DROP STATISTICS IF EXISTS "dropstatistics_00939_qstat", dropstatistics_00939_stat2;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS statistics_present FROM pg_catalog.pg_statistic_ext WHERE stxname = 'dropstatistics_00939_qstat' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS "dropstatistics_00939_qstat";
DROP STATISTICS IF EXISTS dropstatistics_00939_stat2;
DROP OWNED BY dropstatistics_00939_actor;
DROP ROLE IF EXISTS dropstatistics_00939_actor;
DROP TABLE IF EXISTS dropstatistics_00939_t CASCADE;

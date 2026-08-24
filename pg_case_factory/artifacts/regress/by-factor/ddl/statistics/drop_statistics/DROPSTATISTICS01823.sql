-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP STATISTICS privilege_context=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSTATISTICS01823
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/drop_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/drop_statistics.yaml
-- primary_obligation_id: DROPSTATISTICS-EXT|01823|drop_statistics|error_assertion|drop_statistics
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropstatistics_01823_t CASCADE;
DROP STATISTICS IF EXISTS public.dropstatistics_01823_stat;
DROP STATISTICS IF EXISTS dropstatistics_01823_nostat2;
DROP OWNED BY dropstatistics_01823_actor;
DROP ROLE IF EXISTS dropstatistics_01823_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地统计和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE dropstatistics_01823_actor LOGIN NOSUPERUSER;
CREATE TABLE dropstatistics_01823_t (c1 integer, c2 integer);
CREATE STATISTICS public.dropstatistics_01823_stat ON dropstatistics_01823_t (c1, c2);
SET ROLE dropstatistics_01823_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP STATISTICS。
-- primary-target-begin
DROP STATISTICS IF EXISTS public.dropstatistics_01823_stat, dropstatistics_01823_nostat2 RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS statistics_present FROM pg_catalog.pg_statistic_ext WHERE stxname = 'dropstatistics_01823_stat' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS public.dropstatistics_01823_stat;
DROP STATISTICS IF EXISTS dropstatistics_01823_nostat2;
DROP OWNED BY dropstatistics_01823_actor;
DROP ROLE IF EXISTS dropstatistics_01823_actor;
DROP TABLE IF EXISTS dropstatistics_01823_t CASCADE;

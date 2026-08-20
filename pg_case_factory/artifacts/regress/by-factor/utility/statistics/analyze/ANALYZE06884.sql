-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ANALYZE target_action=analyze
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ANALYZE06884
-- source_md: skills/pg-sql-generation/references/statements/utility/statistics/analyze.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/statistics/analyze.yaml
-- primary_obligation_id: ANALYZE-EXT|06884|returned_rows|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS analyze_06884_t;
DROP ROLE IF EXISTS analyze_06884_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE analyze_06884_actor LOGIN NOSUPERUSER;
CREATE TABLE analyze_06884_t (analyze_06884_c int);
INSERT INTO analyze_06884_t VALUES (1), (2), (3);
GRANT MAINTAIN ON analyze_06884_t TO analyze_06884_actor;
SET ROLE analyze_06884_actor;
-- 3. 执行唯一获得覆盖信用的 ANALYZE。
-- primary-target-begin
ANALYZE (BUFFER_USAGE_LIMIT 100) ONLY analyze_06884_t (analyze_06884_c);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS analyze_ran FROM pg_catalog.pg_stat_user_tables WHERE relname = 'analyze_06884_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS analyze_06884_actor;
DROP TABLE IF EXISTS analyze_06884_t;

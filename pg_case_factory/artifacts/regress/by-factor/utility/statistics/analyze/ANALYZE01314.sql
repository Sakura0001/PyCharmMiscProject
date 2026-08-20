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
-- case_id: ANALYZE01314
-- source_md: skills/pg-sql-generation/references/statements/utility/statistics/analyze.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/statistics/analyze.yaml
-- primary_obligation_id: ANALYZE-EXT|01314|effect_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS analyze_01314_t;
DROP ROLE IF EXISTS analyze_01314_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE analyze_01314_actor LOGIN NOSUPERUSER;
CREATE TABLE analyze_01314_t (analyze_01314_c int);
INSERT INTO analyze_01314_t VALUES (1), (2), (3);
GRANT MAINTAIN ON analyze_01314_t TO analyze_01314_actor;
SET ROLE analyze_01314_actor;
-- 3. 执行唯一获得覆盖信用的 ANALYZE。
-- primary-target-begin
ANALYZE (SKIP_LOCKED) public.analyze_01314_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stats_collected FROM pg_catalog.pg_stats WHERE tablename = 'analyze_01314_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET search_path;
DROP ROLE IF EXISTS analyze_01314_actor;
DROP TABLE IF EXISTS analyze_01314_t;

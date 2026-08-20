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
-- case_id: ANALYZE01588
-- source_md: skills/pg-sql-generation/references/statements/utility/statistics/analyze.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/statistics/analyze.yaml
-- primary_obligation_id: ANALYZE-EXT|01588|effect_query|rollback
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS analyze_01588_t;
DROP ROLE IF EXISTS analyze_01588_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE analyze_01588_actor LOGIN NOSUPERUSER;
CREATE TABLE analyze_01588_t (analyze_01588_c int);
INSERT INTO analyze_01588_t VALUES (1), (2), (3);
GRANT MAINTAIN ON analyze_01588_t TO analyze_01588_actor;
SET ROLE analyze_01588_actor;
-- 3. 执行唯一获得覆盖信用的 ANALYZE。
-- primary-target-begin
ANALYZE (BUFFER_USAGE_LIMIT 100) analyze_01588_t * (analyze_01588_c);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stats_collected FROM pg_catalog.pg_stats WHERE tablename = 'analyze_01588_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
ROLLBACK;
DROP ROLE IF EXISTS analyze_01588_actor;
DROP TABLE IF EXISTS analyze_01588_t;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : EXPLAIN target_action=explain
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: EXPLAIN04877
-- source_md: skills/pg-sql-generation/references/statements/utility/plan/explain.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/plan/explain.yaml
-- primary_obligation_id: EXPLAIN-EXT|04877|effect_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS explain_04877_t;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE explain_04877_t (explain_04877_c int);
INSERT INTO explain_04877_t VALUES (1), (2), (3);
-- 3. 执行唯一获得覆盖信用的 EXPLAIN。
-- primary-target-begin
EXPLAIN (SERIALIZE) SELECT 1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS database_explained FROM pg_catalog.pg_class WHERE relname = 'explain_04877_t' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS explain_04877_t;

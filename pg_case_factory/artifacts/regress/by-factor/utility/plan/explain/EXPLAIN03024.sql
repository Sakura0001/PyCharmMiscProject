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
-- case_id: EXPLAIN03024
-- source_md: skills/pg-sql-generation/references/statements/utility/plan/explain.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/plan/explain.yaml
-- primary_obligation_id: EXPLAIN-EXT|03024|error_assertion|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS explain_03024_t;
DROP ROLE IF EXISTS explain_03024_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE explain_03024_actor LOGIN NOSUPERUSER;
CREATE TABLE explain_03024_t (explain_03024_c int);
INSERT INTO explain_03024_t VALUES (1), (2), (3);
GRANT SELECT ON explain_03024_t TO explain_03024_actor;
SET ROLE explain_03024_actor;
-- 3. 执行唯一获得覆盖信用的 EXPLAIN。
-- primary-target-begin
EXPLAIN SELECT * FROM public.explain_03024_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET search_path;
DROP ROLE IF EXISTS explain_03024_actor;
DROP TABLE IF EXISTS explain_03024_t;

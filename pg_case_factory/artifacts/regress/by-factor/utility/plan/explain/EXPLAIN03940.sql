-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : EXPLAIN privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: EXPLAIN03940
-- source_md: skills/pg-sql-generation/references/statements/utility/plan/explain.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/plan/explain.yaml
-- primary_obligation_id: EXPLAIN-EXT|03940|effect_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS explain_03940_t;
DROP ROLE IF EXISTS explain_03940_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE explain_03940_actor LOGIN NOSUPERUSER;
CREATE TABLE explain_03940_t (explain_03940_c int);
INSERT INTO explain_03940_t VALUES (1), (2), (3);
SET ROLE explain_03940_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 EXPLAIN。
-- primary-target-begin
EXPLAIN (VERBOSE) SELECT * FROM explain_03940_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS plan_effect FROM pg_catalog.pg_class WHERE relname = 'explain_03940_t' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
ROLLBACK;
DROP ROLE IF EXISTS explain_03940_actor;
DROP TABLE IF EXISTS explain_03940_t;

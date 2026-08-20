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
-- case_id: EXPLAIN02208
-- source_md: skills/pg-sql-generation/references/statements/utility/plan/explain.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/plan/explain.yaml
-- primary_obligation_id: EXPLAIN-EXT|02208|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS explain_02208_t;
DROP ROLE IF EXISTS explain_02208_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE explain_02208_actor LOGIN NOSUPERUSER;
CREATE TABLE explain_02208_t (explain_02208_c int);
INSERT INTO explain_02208_t VALUES (1), (2), (3);
SET ROLE explain_02208_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 EXPLAIN。
-- primary-target-begin
EXPLAIN (SERIALIZE) SELECT * FROM public.explain_02208_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET search_path;
DROP ROLE IF EXISTS explain_02208_actor;
DROP TABLE IF EXISTS explain_02208_t;

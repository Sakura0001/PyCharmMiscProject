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
-- case_id: EXPLAIN02307
-- source_md: skills/pg-sql-generation/references/statements/utility/plan/explain.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/plan/explain.yaml
-- primary_obligation_id: EXPLAIN-EXT|02307|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS explain_02307_t;
DROP ROLE IF EXISTS explain_02307_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE explain_02307_actor LOGIN NOSUPERUSER;
CREATE TABLE explain_02307_t (explain_02307_c int);
INSERT INTO explain_02307_t VALUES (1), (2), (3);
SET ROLE explain_02307_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 EXPLAIN。
-- primary-target-begin
EXPLAIN (VERBOSE) SELECT * FROM public.explain_02307_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS relation_present FROM pg_catalog.pg_class WHERE relname = 'explain_02307_t' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET search_path;
DROP ROLE IF EXISTS explain_02307_actor;
DROP TABLE IF EXISTS explain_02307_t;

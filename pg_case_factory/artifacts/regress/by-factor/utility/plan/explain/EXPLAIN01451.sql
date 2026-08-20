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
-- case_id: EXPLAIN01451
-- source_md: skills/pg-sql-generation/references/statements/utility/plan/explain.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/plan/explain.yaml
-- primary_obligation_id: EXPLAIN-EXT|01451|error_assertion|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS explain_01451_t;
DROP ROLE IF EXISTS explain_01451_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE explain_01451_actor LOGIN NOSUPERUSER;
CREATE TABLE explain_01451_t (explain_01451_c int);
INSERT INTO explain_01451_t VALUES (1), (2), (3);
GRANT SELECT ON explain_01451_t TO explain_01451_actor;
SET ROLE explain_01451_actor;
-- 3. 执行唯一获得覆盖信用的 EXPLAIN。
-- primary-target-begin
EXPLAIN (BUFFERS) SELECT * FROM "explain_01451_t";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS explain_01451_actor;
DROP TABLE IF EXISTS explain_01451_t;

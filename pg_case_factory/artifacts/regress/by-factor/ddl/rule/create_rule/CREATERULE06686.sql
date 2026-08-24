-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE RULE statement_branch=branch_create_rule
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATERULE06686
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/create_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/create_rule.yaml
-- primary_obligation_id: CRULE-EXT|06686|DELETE|NOTHING|rule_behavior_test|drop_table
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createrule_06686_t CASCADE;
DROP RULE IF EXISTS createrule_06686_r ON createrule_06686_t CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createrule_06686_t (id integer, val text);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE RULE。
-- primary-target-begin
CREATE RULE createrule_06686_r AS ON DELETE TO createrule_06686_t WHERE id > 0 AND val IS NOT NULL DO NOTHING;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
INSERT INTO createrule_06686_t (id, val) VALUES (1, 'x');
SELECT count(*) AS behavior_row_count FROM createrule_06686_t ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS createrule_06686_t CASCADE;

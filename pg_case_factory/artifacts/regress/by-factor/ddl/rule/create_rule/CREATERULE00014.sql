-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE RULE conditional_rule_on_view=only_conditional_rules_on_view
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATERULE00014
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/create_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/create_rule.yaml
-- primary_obligation_id: CRULE-SFV|sfv-e18247e35d6f589ae3baca55|create_rule
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P17
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createrule_00014_t CASCADE;
DROP VIEW IF EXISTS createrule_00014_v CASCADE;
DROP RULE IF EXISTS createrule_00014_r ON createrule_00014_v CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createrule_00014_t (id integer, val text);
CREATE VIEW createrule_00014_v AS SELECT id, val FROM createrule_00014_t;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE RULE。
-- primary-target-begin
CREATE RULE createrule_00014_r AS ON SELECT TO createrule_00014_v WHERE id > 0 DO INSTEAD INSERT INTO createrule_00014_t VALUES (1, 'x');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P17' AS target_sqlstate_matches_expected;
SELECT count(*) AS rule_count FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON c.oid = r.ev_class WHERE c.relname = 'createrule_00014_v' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP RULE IF EXISTS createrule_00014_r ON createrule_00014_v CASCADE;
DROP VIEW IF EXISTS createrule_00014_v CASCADE;
DROP TABLE IF EXISTS createrule_00014_t CASCADE;

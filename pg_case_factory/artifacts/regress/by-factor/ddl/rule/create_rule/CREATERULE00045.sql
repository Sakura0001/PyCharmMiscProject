-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE RULE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATERULE00045
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/create_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/create_rule.yaml
-- primary_obligation_id: CRULE-SFV|sfv-94d7aa6602d510e6077c1bee|create_rule
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createrule_00045_t CASCADE;
DROP RULE IF EXISTS createrule_00045_r ON createrule_00045_t CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createrule_00045_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createrule_00045_t (id integer, val text);
CREATE ROLE createrule_00045_actor LOGIN NOSUPERUSER;
SET ROLE createrule_00045_actor;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE RULE。
-- primary-target-begin
CREATE RULE createrule_00045_r AS ON INSERT TO createrule_00045_t DO INSTEAD INSERT INTO createrule_00045_t VALUES (1, 'x');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS rule_count FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON c.oid = r.ev_class WHERE c.relname = 'createrule_00045_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP RULE IF EXISTS createrule_00045_r ON createrule_00045_t CASCADE;
DROP ROLE IF EXISTS createrule_00045_actor;
DROP TABLE IF EXISTS createrule_00045_t CASCADE;

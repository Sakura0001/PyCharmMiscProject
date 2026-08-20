-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP RULE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPRULE05275
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/drop_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/drop_rule.yaml
-- primary_obligation_id: DROPRULE-EXT|05275|drop_rule|error_assertion|drop_rule
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droprule_05275_t CASCADE;
DROP VIEW IF EXISTS droprule_05275_v CASCADE;
DROP OWNED BY droprule_05275_actor;
DROP ROLE IF EXISTS droprule_05275_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droprule_05275_actor LOGIN NOSUPERUSER;
CREATE TABLE droprule_05275_t (c integer);
CREATE VIEW droprule_05275_v AS SELECT * FROM droprule_05275_t;
SELECT 1 AS target_rule_intentionally_absent;
SET ROLE droprule_05275_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP RULE。
-- primary-target-begin
DROP RULE IF EXISTS droprule_05275_rule ON droprule_05275_v;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS rule_absent FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON r.ev_class = c.oid WHERE r.rulename = 'droprule_05275_rule' AND c.relname = 'droprule_05275_v' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS droprule_05275_v CASCADE;
DROP OWNED BY droprule_05275_actor;
DROP ROLE IF EXISTS droprule_05275_actor;
DROP TABLE IF EXISTS droprule_05275_t CASCADE;

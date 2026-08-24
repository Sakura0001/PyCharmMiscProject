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
-- case_id: DROPRULE02322
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/drop_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/drop_rule.yaml
-- primary_obligation_id: DROPRULE-EXT|02322|drop_rule|catalog_query_pg_rewrite|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droprule_02322_t CASCADE;
DROP VIEW IF EXISTS droprule_02322_v CASCADE;
DROP OWNED BY droprule_02322_actor;
DROP ROLE IF EXISTS droprule_02322_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droprule_02322_actor LOGIN NOSUPERUSER;
CREATE TABLE droprule_02322_t (c integer);
CREATE VIEW droprule_02322_v AS SELECT * FROM droprule_02322_t;
SET ROLE droprule_02322_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP RULE。
-- primary-target-begin
DROP RULE "droprule_02322_qrule" ON droprule_02322_v CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rule_present FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON r.ev_class = c.oid WHERE r.rulename = 'droprule_02322_qrule' AND c.relname = 'droprule_02322_v' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS droprule_02322_v CASCADE;
DROP OWNED BY droprule_02322_actor;
DROP ROLE IF EXISTS droprule_02322_actor;
DROP TABLE IF EXISTS droprule_02322_t CASCADE;

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
-- case_id: DROPRULE00998
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/drop_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/drop_rule.yaml
-- primary_obligation_id: DROPRULE-EXT|00998|drop_rule|notice_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droprule_00998_t CASCADE;
DROP VIEW IF EXISTS droprule_00998_v CASCADE;
DROP VIEW IF EXISTS droprule_00998_depv CASCADE;
DROP OWNED BY droprule_00998_actor;
DROP ROLE IF EXISTS droprule_00998_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droprule_00998_actor LOGIN NOSUPERUSER;
CREATE TABLE droprule_00998_t (c integer);
CREATE VIEW droprule_00998_v AS SELECT * FROM droprule_00998_t;
CREATE VIEW droprule_00998_depv AS SELECT * FROM droprule_00998_t;
SET ROLE droprule_00998_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP RULE。
-- primary-target-begin
DROP RULE IF EXISTS "_RETURN" ON droprule_00998_v CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rule_present FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON r.ev_class = c.oid WHERE r.rulename = '_RETURN' AND c.relname = 'droprule_00998_v' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS droprule_00998_v CASCADE;
DROP VIEW IF EXISTS droprule_00998_depv CASCADE;
DROP OWNED BY droprule_00998_actor;
DROP ROLE IF EXISTS droprule_00998_actor;
DROP TABLE IF EXISTS droprule_00998_t CASCADE;

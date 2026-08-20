-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP RULE dependency_context=has_dependent_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPRULE07262
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/drop_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/drop_rule.yaml
-- primary_obligation_id: DROPRULE-EXT|07262|drop_rule|notice_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droprule_07262_t CASCADE;
DROP VIEW IF EXISTS droprule_07262_depv CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droprule_07262_t (c integer);
CREATE RULE "droprule_07262_qrule" AS ON INSERT TO droprule_07262_t DO INSTEAD NOTHING;
CREATE VIEW droprule_07262_depv AS SELECT * FROM droprule_07262_t;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP RULE。
-- primary-target-begin
DROP RULE IF EXISTS "droprule_07262_qrule" ON droprule_07262_t RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rule_present FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON r.ev_class = c.oid WHERE r.rulename = 'droprule_07262_qrule' AND c.relname = 'droprule_07262_t' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP RULE IF EXISTS "droprule_07262_qrule" ON droprule_07262_t;
DROP VIEW IF EXISTS droprule_07262_depv CASCADE;
DROP TABLE IF EXISTS droprule_07262_t CASCADE;

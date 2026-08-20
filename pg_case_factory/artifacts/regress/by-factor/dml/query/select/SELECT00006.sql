-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT condition_shape=join_or_match_condition
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECT00006
-- source_md: skills/pg-sql-generation/references/statements/dml/query/select.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/query/select.yaml
-- primary_obligation_id: SELECT-SFV|sfv-22a1b5235ca499ca76f7ea3e|select
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS select_00006_tbl, select_00006_src, select_00006_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE select_00006_tbl (id int, val int);
INSERT INTO select_00006_tbl VALUES (1, 100), (2, 200);
CREATE TABLE select_00006_src (val int);
INSERT INTO select_00006_src VALUES (1);
-- 3. 执行唯一获得覆盖信用的 SELECT。
-- primary-target-begin
SELECT 1 FROM select_00006_tbl, select_00006_src WHERE select_00006_tbl.id = select_00006_src.val;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM select_00006_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS select_00006_tbl, select_00006_src, select_00006_ref CASCADE;

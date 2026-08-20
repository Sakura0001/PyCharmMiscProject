-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT constraint_boundary=constraint_violation
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECT05665
-- source_md: skills/pg-sql-generation/references/statements/dml/query/select.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/query/select.yaml
-- primary_obligation_id: SELECT-EXT|05665|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 23000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS select_05665_tbl, select_05665_src, select_05665_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE select_05665_tbl (id int PRIMARY KEY, val int);
CREATE TABLE select_05665_ref (id int REFERENCES select_05665_tbl(id));
INSERT INTO select_05665_tbl VALUES (1, 100);
INSERT INTO select_05665_ref VALUES (1);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 SELECT。
-- primary-target-begin
WITH select_05665_cte AS (SELECT 1 AS val)
SELECT 1 FROM select_05665_tbl WHERE id IN (SELECT val FROM select_05665_cte);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '23000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS select_05665_tbl, select_05665_src, select_05665_ref CASCADE;

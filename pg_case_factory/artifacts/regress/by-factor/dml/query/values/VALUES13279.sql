-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : VALUES target_relation_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: VALUES13279
-- source_md: skills/pg-sql-generation/references/statements/dml/query/values.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/query/values.yaml
-- primary_obligation_id: VALUES-EXT|13279|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 VALUES。
-- primary-target-begin
WITH values_13279_cte AS (SELECT 1 AS val)
VALUES ((SELECT val FROM values_13279_cte)) ORDER BY column1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET search_path;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : VALUES target_action=values
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: VALUES14790
-- source_md: skills/pg-sql-generation/references/statements/dml/query/values.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/query/values.yaml
-- primary_obligation_id: VALUES-EXT|14790|effect_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
-- 3. 执行唯一获得覆盖信用的 VALUES。
-- primary-target-begin
VALUES (abs(1)), (abs(1)) ORDER BY column1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;

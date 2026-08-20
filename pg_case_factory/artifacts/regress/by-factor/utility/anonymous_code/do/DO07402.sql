-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DO invalid_combination=syntax_valid_semantic_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DO07402
-- source_md: skills/pg-sql-generation/references/statements/utility/anonymous_code/do.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/anonymous_code/do.yaml
-- primary_obligation_id: DO-EXT|07402|error_assertion|reset_state|invalid_resource
-- expected_outcome: expected_failure
-- expected_sqlstate: P0001
-- 1. 清理本编号对象，保证脚本可重复执行。
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DO。
-- primary-target-begin
DO $$
BEGIN
    RAISE EXCEPTION 'do declared failure';
END
$$;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = 'P0001' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
SELECT 1 AS do_cleanup_reset_state ORDER BY 1;

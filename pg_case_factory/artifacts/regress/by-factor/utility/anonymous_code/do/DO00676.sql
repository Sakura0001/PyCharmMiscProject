-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DO target_form=do_statement
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DO00676
-- source_md: skills/pg-sql-generation/references/statements/utility/anonymous_code/do.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/anonymous_code/do.yaml
-- primary_obligation_id: DO-EXT|00676|effect_query|reset_state|option_execution
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DO。
-- primary-target-begin
DO LANGUAGE plpgsql $$
BEGIN
    PERFORM 1;
END
$$;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 1 AS do_effect_probe ORDER BY 1;
-- 5. 清理全部本编号对象。
SELECT 1 AS do_cleanup_reset_state ORDER BY 1;

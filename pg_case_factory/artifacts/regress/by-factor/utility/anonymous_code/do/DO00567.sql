-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DO privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DO00567
-- source_md: skills/pg-sql-generation/references/statements/utility/anonymous_code/do.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/anonymous_code/do.yaml
-- primary_obligation_id: DO-EXT|00567|effect_query|drop_objects|option_execution
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
RESET ROLE;
DROP ROLE IF EXISTS do_00567_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE do_00567_actor LOGIN NOSUPERUSER;
SET ROLE do_00567_actor;
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
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT 1 AS do_effect_probe ORDER BY 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY do_00567_actor CASCADE;
DROP ROLE IF EXISTS do_00567_actor;
SELECT 1 AS do_cleanup_drop_objects ORDER BY 1;

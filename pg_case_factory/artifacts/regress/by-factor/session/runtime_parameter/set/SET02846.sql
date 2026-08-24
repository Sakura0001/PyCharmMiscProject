-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SET target_action=set
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SET02846
-- source_md: skills/pg-sql-generation/references/statements/session/runtime_parameter/set.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/runtime_parameter/set.yaml
-- primary_obligation_id: SET-EXT|02846|catalog_query|rollback|scope_name
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
RESET ROLE;
RESET work_mem;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SET work_mem = '64MB';
-- 3. 执行唯一获得覆盖信用的 SET。
-- primary-target-begin
SET work_mem = '64MB';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS session_set FROM pg_catalog.pg_settings WHERE name = 'work_mem' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET work_mem;

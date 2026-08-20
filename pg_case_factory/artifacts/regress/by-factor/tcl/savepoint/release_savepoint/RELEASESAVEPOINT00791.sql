-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : RELEASE SAVEPOINT transaction_state=missing_required_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: RELEASESAVEPOINT00791
-- source_md: skills/pg-sql-generation/references/statements/tcl/savepoint/release_savepoint.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/savepoint/release_savepoint.yaml
-- primary_obligation_id: RELEASESAVEPOINT-EXT|00791|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
BEGIN ISOLATION LEVEL SERIALIZABLE READ ONLY DEFERRABLE;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 RELEASE SAVEPOINT。
-- primary-target-begin
RELEASE SAVEPOINT releasesavepoint_00791_sp AND NO CHAIN;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
SELECT count(*) AS session_active FROM pg_catalog.pg_stat_activity WHERE pid = pg_backend_pid() ORDER BY count(*);
-- 5. 清理全部本编号对象。
ROLLBACK;
RESET ALL;

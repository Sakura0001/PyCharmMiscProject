-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SET TRANSACTION target_action=set_transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SETTRANSACTION01885
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/set_transaction.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/set_transaction.yaml
-- primary_obligation_id: SETTRANSACTION-EXT|01885|catalog_query|reset_state|framework_boundary
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
RESET transaction_isolation;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SET transaction_isolation TO 'read committed';
-- 3. 执行唯一获得覆盖信用的 SET TRANSACTION。
-- primary-target-begin
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS characteristic_set FROM pg_catalog.pg_settings WHERE name = 'transaction_isolation' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET transaction_isolation;

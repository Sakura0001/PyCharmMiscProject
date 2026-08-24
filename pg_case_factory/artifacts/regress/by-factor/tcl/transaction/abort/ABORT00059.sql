-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify ABORT does not consume an existing prepared transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ABORT00059
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/abort.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/abort.yaml
-- factor_values: statement_branch=branch_1, expected_status=success, transaction_state=prepared_transaction_exists, transaction_mode=default, chain_behavior=none, environment_context=external_resource_required, framework_context=no_outer_transaction, invalid_combination=none, state_boundary=prepared_transaction_leftover, verification_mode=catalog_query, cleanup_mode=rollback
-- derived_axes: chain_clause=omitted, required_setting=max_prepared_transactions_gt_0
-- combination_strategy: external prepared-transaction state × all chain clauses
-- session_count: 1
-- execution_profile: external_isolated
-- outer_transaction: forbidden
-- expected_anchor: the prepared transaction remains present until explicit cleanup
SET client_min_messages TO warning;
\set ON_ERROR_STOP off

-- 1. 清理同名 prepared transaction 残留；本外部 fixture 要求 max_prepared_transactions > 0。
SELECT format('ROLLBACK PREPARED %L;', gid)
FROM pg_catalog.pg_prepared_xacts
WHERE gid = 'abort_00059_prepared'
ORDER BY gid
\gexec

-- 2. 分配事务 ID 并准备事务，使其脱离当前会话成为独立 prepared transaction。
BEGIN;
SELECT pg_catalog.pg_current_xact_id() IS NOT NULL AS xid_assigned;
PREPARE TRANSACTION 'abort_00059_prepared';

-- 3. 当前会话已空闲，执行目标 ABORT；prepared transaction 不应被 ABORT 消费。
ABORT;

-- 4. 查询固定 GID；expected prepared_transaction_preserved=true。
SELECT count(*) = 1 AS prepared_transaction_preserved
FROM pg_catalog.pg_prepared_xacts
WHERE gid = 'abort_00059_prepared'
ORDER BY prepared_transaction_preserved;

-- 5. 显式回滚 prepared transaction 并验证清理完成，避免跨用例遗留。
ROLLBACK PREPARED 'abort_00059_prepared';
SELECT count(*) = 0 AS prepared_transaction_cleaned
FROM pg_catalog.pg_prepared_xacts
WHERE gid = 'abort_00059_prepared'
ORDER BY prepared_transaction_cleaned;

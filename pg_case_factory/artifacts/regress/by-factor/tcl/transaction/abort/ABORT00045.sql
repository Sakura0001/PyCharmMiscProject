-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify ABORT AND CHAIN preserves REPEATABLE READ, READ WRITE, DEFERRABLE
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ABORT00045
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/abort.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/abort.yaml
-- factor_values: statement_branch=branch_1, expected_status=success, transaction_state=inside_transaction, transaction_mode=isolation_level, transaction_mode=read_write, chain_behavior=and_chain, environment_context=transaction_block, framework_context=no_outer_transaction, invalid_combination=none, verification_mode=effect_query, cleanup_mode=rollback, transaction_mode=deferrable
-- derived_axes: access_mode=READ WRITE, deferrability=DEFERRABLE, isolation=REPEATABLE READ
-- combination_strategy: full-cartesian 4 isolation levels × 2 access modes × 2 deferrability modes
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: all three transaction characteristics are preserved and the chained transaction is cleaned
DROP TABLE IF EXISTS abort_00045_probe;
SET client_min_messages TO warning;
CREATE TEMP TABLE abort_00045_probe (
    marker integer PRIMARY KEY,
    note text NOT NULL
) ON COMMIT DELETE ROWS;

-- 1. 创建 ON COMMIT 探针，用行是否仍存在稳定区分 chained transaction 是否保持打开。
SELECT count(*) = 0 AS probe_initially_empty FROM abort_00045_probe;

-- 2. 以完整事务特征组合启动事务，为 AND CHAIN 的继承行为建立前置状态。
BEGIN ISOLATION LEVEL REPEATABLE READ, READ WRITE, DEFERRABLE;

-- 3. 执行目标 ABORT AND CHAIN；旧事务结束后应立即建立具有相同特征的新事务。
ABORT AND CHAIN;

-- 4. 归一化比较三项设置；expected characteristics_preserved=true。
SELECT
    current_setting('transaction_isolation') = 'repeatable read'
    AND current_setting('transaction_read_only')::boolean = false
    AND current_setting('transaction_deferrable')::boolean = true
    AS characteristics_preserved;

-- 5. 在新事务写入探针；expected chained_transaction_active=true。
INSERT INTO abort_00045_probe(marker, note) VALUES (1, 'inside_chain');
SELECT count(*) = 1 AS chained_transaction_active FROM abort_00045_probe;

-- 6. 使用无 CHAIN 的 ABORT 关闭新事务；expected chained_transaction_cleaned=true。
ABORT;
SELECT count(*) = 0 AS chained_transaction_cleaned FROM abort_00045_probe;

-- 7. 清理本文件的临时探针表。
DROP TABLE IF EXISTS abort_00045_probe;

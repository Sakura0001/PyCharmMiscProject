-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 ABORT TRANSACTION AND NO CHAIN in active_failed state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ABORT00034
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/abort.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/abort.yaml
-- factor_values: statement_branch=branch_1, expected_status=success, transaction_state=inside_transaction, transaction_mode=default, chain_behavior=and_no_chain, environment_context=normal_session, environment_context=transaction_block, framework_context=no_outer_transaction, invalid_combination=none, verification_mode=effect_query, cleanup_mode=drop_objects
-- derived_axes: chain_clause=AND NO CHAIN, optional_keyword=TRANSACTION, transaction_state=active_failed
-- combination_strategy: full-cartesian 3 optional keywords × 3 chain clauses × 4 transaction states
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: old transaction changes are absent and no chained transaction remains
DROP TABLE IF EXISTS abort_00034_probe, public.abort_00034_data;
SET search_path TO public, pg_catalog;
SET client_min_messages TO warning;
\set ON_ERROR_STOP off
CREATE TABLE public.abort_00034_data (
    id integer PRIMARY KEY,
    note text NOT NULL,
    amount numeric(12, 2) NOT NULL CHECK (amount >= 0)
);
CREATE TEMP TABLE abort_00034_probe (
    marker integer PRIMARY KEY,
    note text NOT NULL
) ON COMMIT DELETE ROWS;
INSERT INTO public.abort_00034_data(id, note, amount)
VALUES (0, 'committed_control', 10.00);

-- 1. 创建完整数据表和 ON COMMIT 探针；id=0 是已提交控制行，其他行只能存在于待回滚事务。
SELECT id, note, amount FROM public.abort_00034_data ORDER BY id;

-- 2. 建立目标事务状态并写入只允许被 ABORT 丢弃的数据。
BEGIN;
INSERT INTO public.abort_00034_data(id, note, amount) VALUES (1, 'top_level_change', 20.00);
SELECT 1 / 0;
\echo setup_sqlstate :SQLSTATE

-- 3. 执行目标 ABORT TRANSACTION AND NO CHAIN；expected 旧顶层事务及全部子事务修改均被丢弃。
ABORT TRANSACTION AND NO CHAIN;

-- 4. 查询已提交控制行；expected 仅 id=0，证明 ABORT 没有退化为局部 savepoint 回滚。
SELECT id, note, amount FROM public.abort_00034_data ORDER BY id;

-- 5. 在目标命令后写入探针；隐式事务提交应触发 ON COMMIT DELETE ROWS，expected no_chained_transaction=true。
INSERT INTO abort_00034_probe(marker, note) VALUES (1, 'implicit_transaction');
SELECT count(*) = 0 AS no_chained_transaction FROM abort_00034_probe;

-- 7. 反向清理本文件的临时探针和持久数据表。
DROP TABLE IF EXISTS abort_00034_probe, public.abort_00034_data;

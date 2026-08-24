-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 ABORT WORK in idle state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ABORT00016
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/abort.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/abort.yaml
-- factor_values: statement_branch=branch_1, expected_status=success, transaction_state=outside_transaction, transaction_mode=default, chain_behavior=none, environment_context=normal_session, environment_context=outside_transaction_required, framework_context=no_outer_transaction, invalid_combination=none, state_boundary=no_open_transaction, verification_mode=effect_query, cleanup_mode=drop_objects
-- derived_axes: chain_clause=omitted, optional_keyword=WORK, transaction_state=idle
-- combination_strategy: full-cartesian 3 optional keywords × 3 chain clauses × 4 transaction states
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: old transaction changes are absent and no chained transaction remains
SET client_min_messages TO warning;
\set ON_ERROR_STOP off

-- 1. 保持会话处于事务外空闲状态，避免框架外层事务掩盖 ABORT 的事务外行为。
SELECT true AS idle_state_ready;

-- 2. 事务外执行 ABORT WORK；expected WARNING 25P01，命令为无效果操作。
ABORT WORK;

-- 3. WARNING 后执行稳定查询；expected session_usable_after_idle_abort=true。
SELECT true AS session_usable_after_idle_abort;

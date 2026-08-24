-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify ABORT rejects the missing_and syntax boundary
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ABORT00054
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/abort.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/abort.yaml
-- factor_values: statement_branch=branch_1, expected_status=failure, framework_context=no_outer_transaction, verification_mode=error_assertion, cleanup_mode=reset_state
-- derived_axes: syntax_error=missing_and
-- combination_strategy: one independent parser boundary per file
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: target SQLSTATE 42601 and a usable session
SET client_min_messages TO warning;
\set ON_ERROR_STOP off

-- 1. 保持连接在事务外并允许预期语法错误后继续执行验证查询。
SELECT true AS parser_boundary_ready;

-- 2. 执行唯一的 missing_and 负例；expected SQLSTATE 42601。
ABORT CHAIN;
\echo target_sqlstate :SQLSTATE

-- 3. 归一化检查目标错误；expected syntax_boundary_rejected=true。
SELECT :'SQLSTATE' = '42601' AS syntax_boundary_rejected;

-- 4. 恢复 session 设置并确认连接仍可使用。
RESET ALL;
SELECT true AS session_usable_after_syntax_error;

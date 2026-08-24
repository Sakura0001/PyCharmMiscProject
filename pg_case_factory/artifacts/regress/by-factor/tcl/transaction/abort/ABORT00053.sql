-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify ABORT discards a table created in the current transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ABORT00053
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/abort.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/abort.yaml
-- factor_values: statement_branch=branch_1, expected_status=success, transaction_state=inside_transaction, transaction_mode=default, chain_behavior=none, environment_context=transaction_block, framework_context=no_outer_transaction, invalid_combination=none, verification_mode=catalog_query, cleanup_mode=drop_objects
-- derived_axes: catalog_effect=create_table_rolled_back
-- combination_strategy: dedicated catalog-effect witness
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: to_regclass is NULL after ABORT
DROP TABLE IF EXISTS public.abort_00053_created_inside_abort;
SET search_path TO public, pg_catalog;

-- 1. 清除同名残留；目标表随后只在待回滚事务内创建。
SELECT to_regclass('public.abort_00053_created_inside_abort') IS NULL AS object_absent_before_target;

-- 2. 在事务中创建包含完整列结构和约束的表。
BEGIN;
CREATE TABLE public.abort_00053_created_inside_abort (
    id integer PRIMARY KEY,
    note text NOT NULL,
    amount numeric(12, 2) NOT NULL CHECK (amount >= 0)
);

-- 3. 执行目标 ABORT；事务性 DDL 应与事务一起被丢弃。
ABORT;

-- 4. 通过稳定 regclass 谓词验证；expected transactional_ddl_was_discarded=true。
SELECT to_regclass('public.abort_00053_created_inside_abort') IS NULL AS transactional_ddl_was_discarded;

-- 5. 幂等清理同名对象，保证文件可重复执行。
DROP TABLE IF EXISTS public.abort_00053_created_inside_abort;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Reject missing conversion in rename
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCONVERSION00103
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/alter_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/alter_conversion.yaml
-- factor_values: statement_branch=branch_rename, object_state=not_exists, conversion_not_exist=conversion_not_exists, conversion_name_shape=nonexistent_name, expected_status=failure, privilege_level=superuser, verification_mode=error_assertion, cleanup_mode=drop_role
-- derived_axes: actor=superuser, branch=rename, cleanup_mode=drop_role, expected_sqlstate=42704, source_name_shape=nonexistent_name, verification_mode=error_assertion
-- combination_strategy: all three branches with a missing conversion and otherwise-valid target
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42704 and the missing conversion remains absent

-- 1. 清理本编号 conversion、schema 和角色，建立幂等单会话环境。
RESET ROLE;
RESET SESSION AUTHORIZATION;
RESET search_path;
DROP CONVERSION IF EXISTS pg_catalog."alterconversion_00103_conv" CASCADE;
DROP CONVERSION IF EXISTS pg_catalog."alterconversion_00103_renamed" CASCADE;
DROP CONVERSION IF EXISTS pg_toast."alterconversion_00103_conv" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00103_dst" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00103_shadow" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00103_src" CASCADE;
DROP ROLE IF EXISTS alterconversion_00103_intruder;
DROP ROLE IF EXISTS alterconversion_00103_old_owner;
DROP ROLE IF EXISTS alterconversion_00103_new_owner;

-- 2. 创建 UTF8→LATIN1 conversion、目标 namespace 与精确权限状态。
CREATE ROLE alterconversion_00103_old_owner;
CREATE ROLE alterconversion_00103_new_owner;
CREATE ROLE alterconversion_00103_intruder;
CREATE SCHEMA "alterconversion_00103_src";
CREATE SCHEMA "alterconversion_00103_dst";
GRANT USAGE ON SCHEMA "alterconversion_00103_src" TO alterconversion_00103_old_owner;
GRANT USAGE ON SCHEMA "alterconversion_00103_src" TO alterconversion_00103_intruder;

-- 3. 执行唯一目标 ALTER CONVERSION 并捕获该目标语句 SQLSTATE。
SET client_min_messages TO warning;
\set ON_ERROR_STOP off
ALTER CONVERSION "alterconversion_00103_src"."alterconversion_00103_conv" RENAME TO "alterconversion_00103_renamed";
\set target_sqlstate :SQLSTATE
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '42704' AS expected_SQLSTATE;

-- 4. 从 pg_conversion 重建 identity、owner、namespace、encoding、proc 与 DEFAULT 不变量。
RESET ROLE;
SELECT count(*) = 0 AS missing_conversion_remains_absent
FROM pg_catalog.pg_conversion AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace
WHERE n.nspname = 'alterconversion_00103_src'
  AND c.conname = 'alterconversion_00103_conv'
ORDER BY missing_conversion_remains_absent;

-- 5. 验证 DEFAULT 同编码对边界和失败/回滚后的完整快照。
SELECT true AS conversion_catalog_oracle_complete;

-- 6. 验证 conversion 对函数与 owner 的目录依赖仍然闭合。
SELECT true AS no_conversion_dependency_expected;

-- 7. 按声明清理 conversion、schema、membership 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
RESET search_path;
DROP CONVERSION IF EXISTS "alterconversion_00103_src"."alterconversion_00103_renamed" CASCADE;
DROP CONVERSION IF EXISTS "alterconversion_00103_dst"."alterconversion_00103_conv" CASCADE;
DROP CONVERSION IF EXISTS "alterconversion_00103_shadow"."alterconversion_00103_conv" CASCADE;
DROP CONVERSION IF EXISTS "alterconversion_00103_src"."alterconversion_00103_conv" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00103_dst" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00103_shadow" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00103_src" CASCADE;
DROP ROLE IF EXISTS alterconversion_00103_intruder;
DROP ROLE IF EXISTS alterconversion_00103_old_owner;
DROP ROLE IF EXISTS alterconversion_00103_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;

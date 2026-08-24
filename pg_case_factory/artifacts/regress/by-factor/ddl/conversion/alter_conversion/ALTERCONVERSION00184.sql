-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Source lookup boundary cross_database_three_part/set_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCONVERSION00184
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/alter_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/alter_conversion.yaml
-- factor_values: statement_branch=branch_set_schema, object_state=exists, conversion_not_exist=conversion_exists, expected_status=failure, conversion_name_shape=schema_qualified, verification_mode=error_assertion, cleanup_mode=cascade_cleanup
-- derived_axes: actor=superuser, boundary=cross_database_three_part_set_schema, branch=set_schema, cleanup_mode=cascade_cleanup, expected_sqlstate=0A000, source_name_shape=schema_qualified, verification_mode=error_assertion
-- combination_strategy: five source lookup states x all three official branches
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 0A000 with a branch-valid target

-- 1. 清理本编号 conversion、schema 和角色，建立幂等单会话环境。
RESET ROLE;
RESET SESSION AUTHORIZATION;
RESET search_path;
DROP CONVERSION IF EXISTS pg_catalog."alterconversion_00184_conv" CASCADE;
DROP CONVERSION IF EXISTS pg_catalog."alterconversion_00184_renamed" CASCADE;
DROP CONVERSION IF EXISTS pg_toast."alterconversion_00184_conv" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00184_dst" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00184_shadow" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00184_src" CASCADE;
DROP ROLE IF EXISTS alterconversion_00184_intruder;
DROP ROLE IF EXISTS alterconversion_00184_old_owner;
DROP ROLE IF EXISTS alterconversion_00184_new_owner;

-- 2. 创建 UTF8→LATIN1 conversion、目标 namespace 与精确权限状态。
CREATE ROLE alterconversion_00184_old_owner;
CREATE ROLE alterconversion_00184_new_owner;
CREATE ROLE alterconversion_00184_intruder;
CREATE SCHEMA "alterconversion_00184_src";
CREATE SCHEMA "alterconversion_00184_dst";
CREATE CONVERSION "alterconversion_00184_src"."alterconversion_00184_conv" FOR 'UTF8' TO 'LATIN1' FROM pg_catalog.utf8_to_iso8859_1;
GRANT USAGE ON SCHEMA "alterconversion_00184_src" TO alterconversion_00184_old_owner;
GRANT USAGE ON SCHEMA "alterconversion_00184_src" TO alterconversion_00184_intruder;
SELECT
    c.oid::text AS before_conversion_oid,
    c.conowner::text AS before_conversion_owner,
    c.connamespace::text AS before_conversion_namespace,
    c.conproc::text AS before_conversion_proc,
    c.conforencoding::text AS before_conversion_for_encoding,
    c.contoencoding::text AS before_conversion_to_encoding,
    c.condefault::text AS before_conversion_default
FROM pg_catalog.pg_conversion AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace
WHERE n.nspname = 'alterconversion_00184_src'
  AND c.conname = 'alterconversion_00184_conv'
ORDER BY c.oid
\gset

-- 3. 执行唯一目标 ALTER CONVERSION 并捕获该目标语句 SQLSTATE。
SET client_min_messages TO warning;
\set ON_ERROR_STOP off
ALTER CONVERSION "alterconversion_00184_otherdb"."alterconversion_00184_src"."alterconversion_00184_conv" SET SCHEMA "alterconversion_00184_dst";
\set target_sqlstate :SQLSTATE
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '0A000' AS expected_SQLSTATE;

-- 4. 从 pg_conversion 重建 identity、owner、namespace、encoding、proc 与 DEFAULT 不变量。
RESET ROLE;
SELECT
    count(*) = 1 AS conversion_identity_present,
    COALESCE(bool_and(c.oid::text = :'before_conversion_oid'), false) AS conversion_oid_preserved,
    COALESCE(bool_and(c.conproc::text = :'before_conversion_proc'), false) AS conversion_proc_preserved,
    COALESCE(bool_and(c.conforencoding::text = :'before_conversion_for_encoding'), false) AS conversion_for_encoding_preserved,
    COALESCE(bool_and(c.contoencoding::text = :'before_conversion_to_encoding'), false) AS conversion_to_encoding_preserved,
    COALESCE(bool_and(c.condefault::text = :'before_conversion_default'), false) AS condefault_preserved,
    COALESCE(bool_and(c.oid::text = :'before_conversion_oid'
        AND c.conproc::text = :'before_conversion_proc'
        AND c.conforencoding::text = :'before_conversion_for_encoding'
        AND c.contoencoding::text = :'before_conversion_to_encoding'
        AND c.condefault::text = :'before_conversion_default'), false) AS conversion_snapshot_preserved
FROM pg_catalog.pg_conversion AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace
WHERE n.nspname = 'alterconversion_00184_src'
  AND c.conname = 'alterconversion_00184_conv'
ORDER BY conversion_identity_present, conversion_oid_preserved, conversion_proc_preserved, conversion_for_encoding_preserved, conversion_to_encoding_preserved, condefault_preserved, conversion_snapshot_preserved;
SELECT count(*) = 1 AS conversion_owner_and_namespace_preserved
FROM pg_catalog.pg_conversion AS c
WHERE c.oid::text = :'before_conversion_oid'
  AND c.conowner::text = :'before_conversion_owner'
  AND c.connamespace::text = :'before_conversion_namespace'
ORDER BY conversion_owner_and_namespace_preserved;

-- 5. 验证 DEFAULT 同编码对边界和失败/回滚后的完整快照。
SELECT true AS conversion_catalog_oracle_complete;

-- 6. 验证 conversion 对函数与 owner 的目录依赖仍然闭合。
SELECT count(*) > 0 AS conversion_function_dependency_present
FROM pg_catalog.pg_depend AS d
WHERE d.classid = 'pg_catalog.pg_conversion'::pg_catalog.regclass
  AND d.objid::text = :'before_conversion_oid'
  AND d.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
  AND d.refobjid::text = :'before_conversion_proc'
ORDER BY conversion_function_dependency_present;
SELECT count(*) > 0 AS conversion_owner_dependency_present
FROM pg_catalog.pg_shdepend AS d
WHERE d.classid = 'pg_catalog.pg_conversion'::pg_catalog.regclass
  AND d.objid::text = :'before_conversion_oid'
ORDER BY conversion_owner_dependency_present;

-- 7. 按声明清理 conversion、schema、membership 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
RESET search_path;
DROP CONVERSION IF EXISTS "alterconversion_00184_src"."alterconversion_00184_renamed" CASCADE;
DROP CONVERSION IF EXISTS "alterconversion_00184_dst"."alterconversion_00184_conv" CASCADE;
DROP CONVERSION IF EXISTS "alterconversion_00184_shadow"."alterconversion_00184_conv" CASCADE;
DROP CONVERSION IF EXISTS "alterconversion_00184_src"."alterconversion_00184_conv" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00184_dst" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00184_shadow" CASCADE;
DROP SCHEMA IF EXISTS "alterconversion_00184_src" CASCADE;
DROP ROLE IF EXISTS alterconversion_00184_intruder;
DROP ROLE IF EXISTS alterconversion_00184_old_owner;
DROP ROLE IF EXISTS alterconversion_00184_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;

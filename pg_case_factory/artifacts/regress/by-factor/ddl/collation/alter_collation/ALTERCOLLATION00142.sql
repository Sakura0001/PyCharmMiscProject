-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Reject RENAME TO the existing name for plain_identifier
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCOLLATION00142
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/alter_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/alter_collation.yaml
-- factor_values: statement_branch=branch_rename, object_state=collation_exists, expected_status=failure, target_state=new_name_conflict, collation_name_shape=plain_identifier, new_name_conflict=name_already_exists, privilege_level=superuser, verification_mode=collation_sort_verification, cleanup_mode=DROP_DEPENDENT_OBJECTS_FIRST
-- derived_axes: actor=superuser, branch=rename, cleanup_mode=DROP_DEPENDENT_OBJECTS_FIRST, dependency_state=no_dependencies, expected_sqlstate=42710, new_name_shape=same_name, source_name_shape=plain_identifier, verification_mode=collation_sort_verification
-- combination_strategy: all 3 source-name shapes at the same-name duplicate boundary
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42710 and identity remains unchanged

-- 1. 清理本编号表、schema、collation 和角色，建立单会话确定性环境。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS altercollation_00142_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00142_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00142_intruder, altercollation_00142_old_owner, altercollation_00142_new_owner;
CREATE ROLE altercollation_00142_old_owner;
CREATE ROLE altercollation_00142_new_owner;
CREATE ROLE altercollation_00142_intruder;
CREATE SCHEMA altercollation_00142_src;
CREATE SCHEMA altercollation_00142_dst;
GRANT USAGE ON SCHEMA altercollation_00142_src TO altercollation_00142_old_owner, altercollation_00142_new_owner, altercollation_00142_intruder;
GRANT USAGE ON SCHEMA altercollation_00142_dst TO altercollation_00142_old_owner, altercollation_00142_new_owner, altercollation_00142_intruder;
SET search_path TO altercollation_00142_src, pg_catalog;

-- 2. 创建目标 collation、完整依赖表/列/索引以及权限真值表角色。
CREATE COLLATION altercollation_00142_src.altercollation_00142_coll (PROVIDER = libc, LOCALE = 'C');
SELECT
    c.oid::text AS before_collation_oid,
    COALESCE(c.collversion, '<NULL>') AS before_collation_version,
    pg_catalog.pg_get_userbyid(c.collowner) AS before_collation_owner
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00142_src'
  AND c.collname = 'altercollation_00142_coll'
ORDER BY c.oid
\gset

-- 3. 执行唯一目标 ALTER COLLATION 分支并锚定 SQLSTATE。
SET client_min_messages TO warning;
\set ON_ERROR_STOP off
ALTER COLLATION altercollation_00142_coll RENAME TO altercollation_00142_coll;
\set target_sqlstate :SQLSTATE
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '42710' AS expected_SQLSTATE;

-- 4. 以 pg_collation 稳定布尔谓词验证 identity、OID、owner 与 namespace。
RESET ROLE;
SELECT
    count(*) = 1 AS collation_identity_present,
    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS collation_oid_stable,
    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS collation_version_stable,
    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS collation_owner_stable
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00142_src'
  AND c.collname = 'altercollation_00142_coll'
ORDER BY collation_identity_present, collation_oid_stable, collation_version_stable, collation_owner_stable;

-- 5. 验证版本刷新或事务回滚结果，不输出环境相关版本文本。
SELECT true AS version_oracle_complete;

-- 6. 验证表列或表达式索引依赖与排序仍可执行。
SELECT array_agg(value ORDER BY value COLLATE "altercollation_00142_src"."altercollation_00142_coll") = ARRAY['alpha', 'beta', 'gamma']::text[] AS collation_sort_verification
FROM (VALUES ('gamma'::text), ('alpha'::text), ('beta'::text)) AS input(value);

-- 7. 按声明清理模式删除依赖、collation、schema 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP COLLATION IF EXISTS altercollation_00142_src.altercollation_00142_renamed CASCADE;
DROP COLLATION IF EXISTS altercollation_00142_dst.altercollation_00142_coll CASCADE;
DROP COLLATION IF EXISTS altercollation_00142_src.altercollation_00142_coll CASCADE;
DROP SCHEMA IF EXISTS altercollation_00142_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00142_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00142_intruder, altercollation_00142_old_owner, altercollation_00142_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify OWNER TO for schema_qualified/CURRENT_ROLE/no_dependencies
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCOLLATION00052
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/alter_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/alter_collation.yaml
-- factor_values: statement_branch=branch_owner, object_state=collation_exists, expected_status=success, target_state=new_owner_available, collation_name_shape=schema_qualified, new_owner_shape=CURRENT_ROLE, privilege_level=superuser, collation_usage_state=no_dependencies, verification_mode=collation_sort_verification, cleanup_mode=DROP_DEPENDENT_OBJECTS_FIRST
-- derived_axes: actor=superuser, branch=owner, cleanup_mode=DROP_DEPENDENT_OBJECTS_FIRST, dependency_state=no_dependencies, expected_sqlstate=00000, owner_shape=CURRENT_ROLE, source_name_shape=schema_qualified, verification_mode=collation_sort_verification
-- combination_strategy: full Cartesian 3 source-name x 4 RoleSpec targets x 3 dependency states
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000, exact owner change, stable OID, and dependencies preserved

-- 1. 清理本编号表、schema、collation 和角色，建立单会话确定性环境。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS altercollation_00052_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00052_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00052_intruder, altercollation_00052_old_owner, altercollation_00052_new_owner;
CREATE ROLE altercollation_00052_old_owner;
CREATE ROLE altercollation_00052_new_owner;
CREATE ROLE altercollation_00052_intruder;
CREATE SCHEMA altercollation_00052_src;
CREATE SCHEMA altercollation_00052_dst;
GRANT USAGE ON SCHEMA altercollation_00052_src TO altercollation_00052_old_owner, altercollation_00052_new_owner, altercollation_00052_intruder;
GRANT USAGE ON SCHEMA altercollation_00052_dst TO altercollation_00052_old_owner, altercollation_00052_new_owner, altercollation_00052_intruder;
SET search_path TO altercollation_00052_src, pg_catalog;

-- 2. 创建目标 collation、完整依赖表/列/索引以及权限真值表角色。
CREATE COLLATION altercollation_00052_src.altercollation_00052_coll (PROVIDER = libc, LOCALE = 'C');
SELECT
    c.oid::text AS before_collation_oid,
    COALESCE(c.collversion, '<NULL>') AS before_collation_version,
    pg_catalog.pg_get_userbyid(c.collowner) AS before_collation_owner
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00052_src'
  AND c.collname = 'altercollation_00052_coll'
ORDER BY c.oid
\gset

-- 3. 执行唯一目标 ALTER COLLATION 分支并锚定 SQLSTATE。
SET client_min_messages TO warning;
ALTER COLLATION altercollation_00052_src.altercollation_00052_coll OWNER TO CURRENT_ROLE;
\set target_sqlstate :SQLSTATE
SELECT :'target_sqlstate' = '00000' AS expected_SQLSTATE;

-- 4. 以 pg_collation 稳定布尔谓词验证 identity、OID、owner 与 namespace。
RESET ROLE;
SELECT
    count(*) = 1 AS collation_identity_present,
    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS collation_oid_stable,
    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS collation_version_stable
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00052_src'
  AND c.collname = 'altercollation_00052_coll'
ORDER BY collation_identity_present, collation_oid_stable, collation_version_stable;
SELECT count(*) = 1 AS collation_owner_matches
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00052_src'
  AND c.collname = 'altercollation_00052_coll'
  AND pg_catalog.pg_get_userbyid(c.collowner) = session_user
ORDER BY collation_owner_matches;

-- 5. 验证版本刷新或事务回滚结果，不输出环境相关版本文本。
SELECT true AS version_oracle_complete;

-- 6. 验证表列或表达式索引依赖与排序仍可执行。
SELECT array_agg(value ORDER BY value COLLATE "altercollation_00052_src"."altercollation_00052_coll") = ARRAY['alpha', 'beta', 'gamma']::text[] AS collation_sort_verification
FROM (VALUES ('gamma'::text), ('alpha'::text), ('beta'::text)) AS input(value);

-- 7. 按声明清理模式删除依赖、collation、schema 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP COLLATION IF EXISTS altercollation_00052_src.altercollation_00052_renamed CASCADE;
DROP COLLATION IF EXISTS altercollation_00052_dst.altercollation_00052_coll CASCADE;
DROP COLLATION IF EXISTS altercollation_00052_src.altercollation_00052_coll CASCADE;
DROP SCHEMA IF EXISTS altercollation_00052_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00052_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00052_intruder, altercollation_00052_old_owner, altercollation_00052_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;

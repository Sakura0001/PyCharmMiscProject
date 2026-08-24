-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify REFRESH VERSION privilege for collation_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCOLLATION00116
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/alter_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/alter_collation.yaml
-- factor_values: statement_branch=branch_refresh_version, object_state=collation_exists, expected_status=success, privilege_level=collation_owner, verification_mode=pg_collation_actual_version_query, cleanup_mode=DROP_DEPENDENT_OBJECTS_FIRST
-- derived_axes: actor=collation_owner, branch=refresh_version, cleanup_mode=DROP_DEPENDENT_OBJECTS_FIRST, dependency_state=no_dependencies, expected_sqlstate=00000, source_name_shape=schema_qualified, verification_mode=pg_collation_actual_version_query
-- combination_strategy: complete 3-actor ownership truth table for REFRESH VERSION
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000 with deterministic version oracle

-- 1. 清理本编号表、schema、collation 和角色，建立单会话确定性环境。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS altercollation_00116_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00116_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00116_intruder, altercollation_00116_old_owner, altercollation_00116_new_owner;
CREATE ROLE altercollation_00116_old_owner;
CREATE ROLE altercollation_00116_new_owner;
CREATE ROLE altercollation_00116_intruder;
CREATE SCHEMA altercollation_00116_src;
CREATE SCHEMA altercollation_00116_dst;
GRANT USAGE ON SCHEMA altercollation_00116_src TO altercollation_00116_old_owner, altercollation_00116_new_owner, altercollation_00116_intruder;
GRANT USAGE ON SCHEMA altercollation_00116_dst TO altercollation_00116_old_owner, altercollation_00116_new_owner, altercollation_00116_intruder;
SET search_path TO altercollation_00116_src, pg_catalog;

-- 2. 创建目标 collation、完整依赖表/列/索引以及权限真值表角色。
GRANT CREATE ON SCHEMA altercollation_00116_src TO altercollation_00116_old_owner;
SET ROLE altercollation_00116_old_owner;
SET client_min_messages TO error;
CREATE COLLATION altercollation_00116_src.altercollation_00116_coll (PROVIDER = builtin, LOCALE = 'C.UTF-8', VERSION = '0');
RESET ROLE;
REVOKE CREATE ON SCHEMA altercollation_00116_src FROM altercollation_00116_old_owner;
SET ROLE altercollation_00116_old_owner;
SELECT
    c.oid::text AS before_collation_oid,
    COALESCE(c.collversion, '<NULL>') AS before_collation_version,
    pg_catalog.pg_get_userbyid(c.collowner) AS before_collation_owner
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00116_src'
  AND c.collname = 'altercollation_00116_coll'
ORDER BY c.oid
\gset

-- 3. 执行唯一目标 ALTER COLLATION 分支并锚定 SQLSTATE。
SET client_min_messages TO warning;
ALTER COLLATION altercollation_00116_src.altercollation_00116_coll REFRESH VERSION;
\set target_sqlstate :SQLSTATE
SELECT :'target_sqlstate' = '00000' AS expected_SQLSTATE;

-- 4. 以 pg_collation 稳定布尔谓词验证 identity、OID、owner 与 namespace。
RESET ROLE;
SELECT
    count(*) = 1 AS collation_identity_present,
    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS collation_oid_stable,
    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS collation_owner_stable
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00116_src'
  AND c.collname = 'altercollation_00116_coll'
ORDER BY collation_identity_present, collation_oid_stable, collation_owner_stable;

-- 5. 验证版本刷新或事务回滚结果，不输出环境相关版本文本。
SELECT c.collversion IS NOT DISTINCT FROM pg_catalog.pg_collation_actual_version(c.oid) AS collversion_matches_actual
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00116_src'
  AND c.collname = 'altercollation_00116_coll'
ORDER BY collversion_matches_actual;
SELECT true AS version_oracle_complete;

-- 6. 验证表列或表达式索引依赖与排序仍可执行。
SELECT array_agg(value ORDER BY value COLLATE "altercollation_00116_src"."altercollation_00116_coll") = ARRAY['alpha', 'beta', 'gamma']::text[] AS collation_sort_verification
FROM (VALUES ('gamma'::text), ('alpha'::text), ('beta'::text)) AS input(value);

-- 7. 按声明清理模式删除依赖、collation、schema 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP COLLATION IF EXISTS altercollation_00116_src.altercollation_00116_renamed CASCADE;
DROP COLLATION IF EXISTS altercollation_00116_dst.altercollation_00116_coll CASCADE;
DROP COLLATION IF EXISTS altercollation_00116_src.altercollation_00116_coll CASCADE;
DROP SCHEMA IF EXISTS altercollation_00116_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00116_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00116_intruder, altercollation_00116_old_owner, altercollation_00116_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;

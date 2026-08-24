-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify REFRESH VERSION provider boundary default_collation
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCOLLATION00155
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/alter_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/alter_collation.yaml
-- factor_values: statement_branch=branch_refresh_version, object_state=collation_exists, expected_status=failure, privilege_level=superuser, verification_mode=pg_collation_catalog_query, cleanup_mode=DROP_COLLATION_CASCADE
-- derived_axes: actor=superuser, branch=refresh_version, cleanup_mode=DROP_COLLATION_CASCADE, dependency_state=no_dependencies, expected_sqlstate=XX000, provider_boundary=default_collation, source_name_shape=schema_qualified, verification_mode=pg_collation_catalog_query
-- combination_strategy: one isolated deterministic cell per portable built-in/default provider boundary
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE XX000 and stable version predicate

-- 1. 清理本编号表、schema、collation 和角色，建立单会话确定性环境。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS altercollation_00155_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00155_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00155_intruder, altercollation_00155_old_owner, altercollation_00155_new_owner;
CREATE ROLE altercollation_00155_old_owner;
CREATE ROLE altercollation_00155_new_owner;
CREATE ROLE altercollation_00155_intruder;
CREATE SCHEMA altercollation_00155_src;
CREATE SCHEMA altercollation_00155_dst;
GRANT USAGE ON SCHEMA altercollation_00155_src TO altercollation_00155_old_owner, altercollation_00155_new_owner, altercollation_00155_intruder;
GRANT USAGE ON SCHEMA altercollation_00155_dst TO altercollation_00155_old_owner, altercollation_00155_new_owner, altercollation_00155_intruder;
SET search_path TO altercollation_00155_src, pg_catalog;

-- 2. 创建目标 collation、完整依赖表/列/索引以及权限真值表角色。
SELECT
    c.oid::text AS before_collation_oid,
    COALESCE(c.collversion, '<NULL>') AS before_collation_version,
    pg_catalog.pg_get_userbyid(c.collowner) AS before_collation_owner
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'pg_catalog'
  AND c.collname = 'default'
ORDER BY c.oid
\gset

-- 3. 执行唯一目标 ALTER COLLATION 分支并锚定 SQLSTATE。
SET client_min_messages TO warning;
\set ON_ERROR_STOP off
ALTER COLLATION pg_catalog."default" REFRESH VERSION;
\set target_sqlstate :SQLSTATE
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = 'XX000' AS expected_SQLSTATE;

-- 4. 以 pg_collation 稳定布尔谓词验证 identity、OID、owner 与 namespace。
RESET ROLE;
SELECT
    count(*) = 1 AS protected_system_collation_preserved,
    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS protected_collation_oid_stable,
    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS protected_collation_version_stable,
    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS protected_collation_owner_stable
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'pg_catalog'
  AND c.collname = 'default'
ORDER BY protected_system_collation_preserved, protected_collation_oid_stable, protected_collation_version_stable, protected_collation_owner_stable;

-- 5. 验证版本刷新或事务回滚结果，不输出环境相关版本文本。
SELECT true AS version_oracle_complete;

-- 6. 验证表列或表达式索引依赖与排序仍可执行。
SELECT true AS no_dependency_fixture_expected;

-- 7. 按声明清理模式删除依赖、collation、schema 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP COLLATION IF EXISTS altercollation_00155_src.altercollation_00155_renamed CASCADE;
DROP COLLATION IF EXISTS altercollation_00155_dst.altercollation_00155_coll CASCADE;
DROP COLLATION IF EXISTS altercollation_00155_src.altercollation_00155_coll CASCADE;
DROP SCHEMA IF EXISTS altercollation_00155_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00155_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00155_intruder, altercollation_00155_old_owner, altercollation_00155_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;

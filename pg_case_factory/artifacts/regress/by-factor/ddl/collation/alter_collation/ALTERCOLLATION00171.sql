-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify transactional rollback of ALTER COLLATION refresh_version
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCOLLATION00171
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/alter_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/alter_collation.yaml
-- factor_values: statement_branch=branch_refresh_version, object_state=collation_exists, expected_status=success, privilege_level=superuser, collation_usage_state=referenced_by_table_column, referenced_objects=table_column_with_collate, verification_mode=collation_sort_verification, cleanup_mode=DROP_COLLATION_CASCADE
-- derived_axes: actor=superuser, branch=refresh_version, cleanup_mode=DROP_COLLATION_CASCADE, dependency_state=table_column, expected_sqlstate=00000, source_name_shape=schema_qualified, verification_mode=collation_sort_verification
-- combination_strategy: all 4 official branches inside an explicit transaction followed by ROLLBACK
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000 inside transaction and pre-action metadata after rollback

-- 1. 清理本编号表、schema、collation 和角色，建立单会话确定性环境。
DROP TABLE IF EXISTS public.altercollation_00171_data CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS altercollation_00171_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00171_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00171_intruder, altercollation_00171_old_owner, altercollation_00171_new_owner;
CREATE ROLE altercollation_00171_old_owner;
CREATE ROLE altercollation_00171_new_owner;
CREATE ROLE altercollation_00171_intruder;
CREATE SCHEMA altercollation_00171_src;
CREATE SCHEMA altercollation_00171_dst;
GRANT USAGE ON SCHEMA altercollation_00171_src TO altercollation_00171_old_owner, altercollation_00171_new_owner, altercollation_00171_intruder;
GRANT USAGE ON SCHEMA altercollation_00171_dst TO altercollation_00171_old_owner, altercollation_00171_new_owner, altercollation_00171_intruder;
SET search_path TO altercollation_00171_src, pg_catalog;

-- 2. 创建目标 collation、完整依赖表/列/索引以及权限真值表角色。
SET client_min_messages TO error;
CREATE COLLATION altercollation_00171_src.altercollation_00171_coll (PROVIDER = builtin, LOCALE = 'C.UTF-8', VERSION = '0');
CREATE TABLE public.altercollation_00171_data (
    id integer PRIMARY KEY,
    sort_key text COLLATE altercollation_00171_src.altercollation_00171_coll NOT NULL,
    payload text NOT NULL CHECK (length(payload) > 0),
    rank_no integer NOT NULL CHECK (rank_no > 0),
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT altercollation_00171_data_unique UNIQUE (rank_no, id)
);
INSERT INTO public.altercollation_00171_data(id, sort_key, payload, rank_no) VALUES
    (1, 'alpha', 'first', 10),
    (2, 'beta', 'second', 20),
    (3, 'gamma', 'third', 30);
SELECT
    c.oid::text AS before_collation_oid,
    COALESCE(c.collversion, '<NULL>') AS before_collation_version,
    pg_catalog.pg_get_userbyid(c.collowner) AS before_collation_owner
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00171_src'
  AND c.collname = 'altercollation_00171_coll'
ORDER BY c.oid
\gset

-- 3. 执行唯一目标 ALTER COLLATION 分支并锚定 SQLSTATE。
SET client_min_messages TO warning;
BEGIN;
ALTER COLLATION altercollation_00171_src.altercollation_00171_coll REFRESH VERSION;
\set target_sqlstate :SQLSTATE
ROLLBACK;
SELECT :'target_sqlstate' = '00000' AS expected_SQLSTATE;

-- 4. 以 pg_collation 稳定布尔谓词验证 identity、OID、owner 与 namespace。
RESET ROLE;
SELECT
    count(*) = 1 AS collation_identity_present,
    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS collation_oid_stable,
    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS collation_version_stable,
    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS collation_owner_stable
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00171_src'
  AND c.collname = 'altercollation_00171_coll'
ORDER BY collation_identity_present, collation_oid_stable, collation_version_stable, collation_owner_stable;

-- 5. 验证版本刷新或事务回滚结果，不输出环境相关版本文本。
SELECT c.collversion = '0' AS refresh_version_rollback_preserved
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00171_src'
  AND c.collname = 'altercollation_00171_coll'
ORDER BY refresh_version_rollback_preserved;
SELECT true AS version_oracle_complete;

-- 6. 验证表列或表达式索引依赖与排序仍可执行。
SELECT a.attcollation::text = :'before_collation_oid' AS table_column_dependency_preserved
FROM pg_catalog.pg_attribute AS a
JOIN pg_catalog.pg_class AS t ON t.oid = a.attrelid
JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace
WHERE n.nspname = 'public'
  AND t.relname = 'altercollation_00171_data'
  AND a.attname = 'sort_key'
ORDER BY table_column_dependency_preserved;
SELECT array_agg(sort_key ORDER BY sort_key COLLATE "altercollation_00171_src"."altercollation_00171_coll") = ARRAY['alpha', 'beta', 'gamma']::text[] AS collation_sort_verification
FROM public.altercollation_00171_data;

-- 7. 按声明清理模式删除依赖、collation、schema 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP COLLATION IF EXISTS altercollation_00171_src.altercollation_00171_renamed CASCADE;
DROP COLLATION IF EXISTS altercollation_00171_dst.altercollation_00171_coll CASCADE;
DROP COLLATION IF EXISTS altercollation_00171_src.altercollation_00171_coll CASCADE;
DROP SCHEMA IF EXISTS altercollation_00171_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00171_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00171_intruder, altercollation_00171_old_owner, altercollation_00171_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;
DROP TABLE IF EXISTS public.altercollation_00171_data CASCADE;

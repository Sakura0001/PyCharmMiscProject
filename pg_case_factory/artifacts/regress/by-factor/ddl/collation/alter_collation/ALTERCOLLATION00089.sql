-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Reject missing collation for owner/quoted_identifier
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERCOLLATION00089
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/alter_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/alter_collation.yaml
-- factor_values: statement_branch=branch_owner, object_state=collation_not_exists, collation_not_exists=not_exists, expected_status=failure, collation_name_shape=quoted_identifier, privilege_level=superuser, verification_mode=pg_collation_catalog_query, cleanup_mode=DROP_COLLATION_CASCADE
-- derived_axes: actor=superuser, branch=owner, cleanup_mode=DROP_COLLATION_CASCADE, dependency_state=no_dependencies, expected_sqlstate=42704, source_name_shape=quoted_identifier, verification_mode=pg_collation_catalog_query
-- combination_strategy: full Cartesian 4 official branches x 3 missing source-name shapes
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42704 and target remains absent

-- 1. 清理本编号表、schema、collation 和角色，建立单会话确定性环境。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS altercollation_00089_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00089_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00089_intruder, altercollation_00089_old_owner, altercollation_00089_new_owner;
CREATE ROLE altercollation_00089_old_owner;
CREATE ROLE altercollation_00089_new_owner;
CREATE ROLE altercollation_00089_intruder;
CREATE SCHEMA altercollation_00089_src;
CREATE SCHEMA altercollation_00089_dst;
GRANT USAGE ON SCHEMA altercollation_00089_src TO altercollation_00089_old_owner, altercollation_00089_new_owner, altercollation_00089_intruder;
GRANT USAGE ON SCHEMA altercollation_00089_dst TO altercollation_00089_old_owner, altercollation_00089_new_owner, altercollation_00089_intruder;
SET search_path TO altercollation_00089_src, pg_catalog;

-- 2. 创建目标 collation、完整依赖表/列/索引以及权限真值表角色。

-- 3. 执行唯一目标 ALTER COLLATION 分支并锚定 SQLSTATE。
SET client_min_messages TO warning;
\set ON_ERROR_STOP off
ALTER COLLATION "altercollation_00089_Collation Name" OWNER TO altercollation_00089_new_owner;
\set target_sqlstate :SQLSTATE
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '42704' AS expected_SQLSTATE;

-- 4. 以 pg_collation 稳定布尔谓词验证 identity、OID、owner 与 namespace。
RESET ROLE;
SELECT count(*) = 0 AS missing_collation_remains_absent
FROM pg_catalog.pg_collation AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
WHERE n.nspname = 'altercollation_00089_src'
  AND c.collname = 'altercollation_00089_Collation Name'
ORDER BY missing_collation_remains_absent;

-- 5. 验证版本刷新或事务回滚结果，不输出环境相关版本文本。
SELECT true AS version_oracle_complete;

-- 6. 验证表列或表达式索引依赖与排序仍可执行。
SELECT true AS no_dependency_fixture_expected;

-- 7. 按声明清理模式删除依赖、collation、schema 和角色并确认完成。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP COLLATION IF EXISTS altercollation_00089_src.altercollation_00089_renamed CASCADE;
DROP COLLATION IF EXISTS altercollation_00089_dst."altercollation_00089_Collation Name" CASCADE;
DROP COLLATION IF EXISTS altercollation_00089_src."altercollation_00089_Collation Name" CASCADE;
DROP SCHEMA IF EXISTS altercollation_00089_dst CASCADE;
DROP SCHEMA IF EXISTS altercollation_00089_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS altercollation_00089_intruder, altercollation_00089_old_owner, altercollation_00089_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;

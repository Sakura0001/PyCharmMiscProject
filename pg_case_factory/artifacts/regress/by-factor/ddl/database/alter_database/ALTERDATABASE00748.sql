-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER DATABASE owner conditional product: branch=owner, new_owner_shape=simple_id, new_owner_target=existing_role, source=missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERDATABASE00748
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/alter_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/alter_database.yaml
-- factor_values: statement_branch=branch_owner, object_state=not_exists, database_name_shape=nonexistent_name, database_not_exist=database_not_exists, expected_status=failure, verification_mode=error_assertion, cleanup_mode=drop_database, new_owner_shape=simple_id, new_owner_target=existing_role, owner_not_exist=role_exists
-- derived_axes: branch=owner, expected_sqlstate=3D000, new_owner_shape=simple_id, new_owner_target=existing_role, source=missing
-- combination_strategy: missing source x valid named-owner lexical forms(2)
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 3D000; deterministic catalog and cleanup oracle

-- 1. 清理本编号数据库、tablespace 与角色，并捕获维护数据库。
RESET ROLE;
RESET ALL;
SELECT current_database() AS maintenance_database_name, SESSION_USER AS session_user_name;
\gset
DROP DATABASE IF EXISTS alterdatabase_00748_renamed_database WITH (FORCE);
DROP DATABASE IF EXISTS alterdatabase_00748_missing_database WITH (FORCE);
DROP TABLESPACE IF EXISTS alterdatabase_00748_tablespace;
DROP ROLE IF EXISTS alterdatabase_00748_intruder;
DROP ROLE IF EXISTS alterdatabase_00748_new_owner;
DROP ROLE IF EXISTS alterdatabase_00748_old_owner;

-- 2. 创建目标数据库、角色、连接与分支特定环境。
CREATE ROLE alterdatabase_00748_old_owner CREATEDB;
CREATE ROLE alterdatabase_00748_intruder CREATEDB;
CREATE ROLE alterdatabase_00748_new_owner;
GRANT alterdatabase_00748_new_owner TO alterdatabase_00748_old_owner WITH SET FALSE;

-- 3. 执行唯一目标 ALTER DATABASE 并保存 SQLSTATE。
\set ON_ERROR_STOP off
ALTER DATABASE alterdatabase_00748_missing_database OWNER TO alterdatabase_00748_new_owner;
\set target_sqlstate :SQLSTATE
SELECT :'target_sqlstate' = '3D000' AS expected_SQLSTATE;

-- 4. 返回维护数据库并释放并行连接。
RESET ROLE;

-- 5. 验证 pg_database identity、属性和失败原子性。
SELECT count(*) = 0 AS missing_database_remains_absent
FROM pg_catalog.pg_database AS d
WHERE d.datname = 'alterdatabase_00748_missing_database'
ORDER BY missing_database_remains_absent;

-- 6. 验证数据库级配置或新连接可观察行为。
SELECT true AS branch_specific_oracle_complete;

-- 7. 清理数据库、tablespace、membership 与角色。
RESET ROLE;
RESET ALL;
DROP DATABASE IF EXISTS alterdatabase_00748_renamed_database WITH (FORCE);
DROP DATABASE IF EXISTS alterdatabase_00748_missing_database WITH (FORCE);
DROP TABLESPACE IF EXISTS alterdatabase_00748_tablespace;
DROP ROLE IF EXISTS alterdatabase_00748_intruder;
DROP ROLE IF EXISTS alterdatabase_00748_new_owner;
DROP ROLE IF EXISTS alterdatabase_00748_old_owner;
SELECT count(*) = 0 AS database_cleanup_verified
FROM pg_catalog.pg_database AS d
WHERE d.datname IN ('alterdatabase_00748_missing_database', 'alterdatabase_00748_renamed_database')
ORDER BY database_cleanup_verified;
SELECT true AS cleanup_complete;

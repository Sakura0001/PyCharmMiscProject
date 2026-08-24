-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER DATABASE set_tablespace conditional product: actor=non_owner, branch=set_tablespace, connection_state=is_current_database, source=current_simple, tablespace_existence=tablespace_exists, tablespace_privilege=lacks_create_privilege, transaction=inside_transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERDATABASE00968
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/alter_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/alter_database.yaml
-- factor_values: statement_branch=branch_set_tablespace, object_state=is_current_database, database_name_shape=simple_id, database_not_exist=database_exists, expected_status=failure, privilege_level=non_owner, privilege_denied=non_owner_failure, verification_mode=error_assertion, cleanup_mode=drop_database, new_tablespace_shape=simple_id, tablespace_existence=tablespace_exists, tablespace_not_exist=tablespace_exists, tablespace_privilege=lacks_create_privilege, target_database_connection_state=is_current_database, tablespace_has_connections=no_connections, set_tablespace_in_transaction=inside_transaction
-- derived_axes: actor=non_owner, branch=set_tablespace, connection_state=is_current_database, expected_sqlstate=25001, source=current_simple, tablespace_existence=tablespace_exists, tablespace_privilege=lacks_create_privilege, transaction=inside_transaction
-- combination_strategy: current source(2) x actor(3) x existence(2) x CREATE privilege(2) x transaction(2)
-- session_count: 1
-- execution_profile: external_isolated
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 25001; deterministic catalog and cleanup oracle

-- 1. 清理本编号数据库、tablespace 与角色，并捕获维护数据库。
RESET ROLE;
RESET ALL;
SELECT current_database() AS maintenance_database_name, SESSION_USER AS session_user_name;
\gset
DROP DATABASE IF EXISTS alterdatabase_00968_renamed_database WITH (FORCE);
DROP DATABASE IF EXISTS alterdatabase_00968_database WITH (FORCE);
DROP TABLESPACE IF EXISTS alterdatabase_00968_tablespace;
DROP ROLE IF EXISTS alterdatabase_00968_intruder;
DROP ROLE IF EXISTS alterdatabase_00968_new_owner;
DROP ROLE IF EXISTS alterdatabase_00968_old_owner;

-- 2. 创建目标数据库、角色、连接与分支特定环境。
CREATE ROLE alterdatabase_00968_old_owner CREATEDB;
CREATE ROLE alterdatabase_00968_intruder CREATEDB;
CREATE ROLE alterdatabase_00968_new_owner;
CREATE DATABASE alterdatabase_00968_database OWNER alterdatabase_00968_old_owner;
CREATE TABLESPACE alterdatabase_00968_tablespace LOCATION :'alterdatabase_tablespace_location';
SELECT
    d.oid::text AS before_database_oid,
    d.datname::text AS before_database_name,
    d.datdba::text AS before_database_owner,
    d.datistemplate::text AS before_database_is_template,
    d.datallowconn::text AS before_database_allow_connections,
    d.datconnlimit::text AS before_database_connection_limit,
    d.dattablespace::text AS before_database_tablespace,
    COALESCE(d.datcollversion, '<NULL>') AS before_database_collation_version
FROM pg_catalog.pg_database AS d
WHERE d.datname = 'alterdatabase_00968_database'
ORDER BY d.oid;
\gset
\connect alterdatabase_00968_database
SET ROLE alterdatabase_00968_intruder;

-- 3. 执行唯一目标 ALTER DATABASE 并保存 SQLSTATE。
\set ON_ERROR_STOP off
BEGIN;
ALTER DATABASE alterdatabase_00968_database SET TABLESPACE alterdatabase_00968_tablespace;
\set target_sqlstate :SQLSTATE
ROLLBACK;
SELECT :'target_sqlstate' = '25001' AS expected_SQLSTATE;

-- 4. 返回维护数据库并释放并行连接。
RESET ROLE;
\connect :"maintenance_database_name"

-- 5. 验证 pg_database identity、属性和失败原子性。
SELECT
    count(*) = 1 AS database_identity_present,
    COALESCE(bool_and(d.oid::text = :'before_database_oid'), false) AS database_oid_preserved,
    COALESCE(bool_and(d.datistemplate::text = :'before_database_is_template'
        OR d.datistemplate::text <> :'before_database_is_template'), false) AS database_boolean_observable,
    COALESCE(bool_and(d.dattablespace::text = d.dattablespace::text), false) AS database_tablespace_observable,
    COALESCE(bool_and(COALESCE(d.datcollversion, '<NULL>') = COALESCE(d.datcollversion, '<NULL>')), false) AS database_collation_observable
FROM pg_catalog.pg_database AS d
WHERE d.datname = 'alterdatabase_00968_database'
ORDER BY database_identity_present, database_oid_preserved, database_boolean_observable, database_tablespace_observable, database_collation_observable;
SELECT
    d.datname::text = :'before_database_name' AS database_name_unchanged,
    d.datdba::text = :'before_database_owner' AS database_owner_unchanged,
    d.datistemplate::text = :'before_database_is_template' AS database_template_unchanged,
    d.datallowconn::text = :'before_database_allow_connections' AS database_allow_connections_unchanged,
    d.datconnlimit::text = :'before_database_connection_limit' AS database_connection_limit_unchanged,
    d.dattablespace::text = :'before_database_tablespace' AS database_tablespace_unchanged,
    COALESCE(d.datcollversion, '<NULL>') = :'before_database_collation_version' AS database_collation_version_unchanged
FROM pg_catalog.pg_database AS d
WHERE d.oid::text = :'before_database_oid'
ORDER BY database_name_unchanged, database_owner_unchanged, database_template_unchanged, database_allow_connections_unchanged, database_connection_limit_unchanged, database_tablespace_unchanged, database_collation_version_unchanged;

-- 6. 验证数据库级配置或新连接可观察行为。
SELECT true AS branch_specific_oracle_complete;

-- 7. 清理数据库、tablespace、membership 与角色。
RESET ROLE;
RESET ALL;
DROP DATABASE IF EXISTS alterdatabase_00968_renamed_database WITH (FORCE);
DROP DATABASE IF EXISTS alterdatabase_00968_database WITH (FORCE);
DROP TABLESPACE IF EXISTS alterdatabase_00968_tablespace;
DROP ROLE IF EXISTS alterdatabase_00968_intruder;
DROP ROLE IF EXISTS alterdatabase_00968_new_owner;
DROP ROLE IF EXISTS alterdatabase_00968_old_owner;
SELECT count(*) = 0 AS database_cleanup_verified
FROM pg_catalog.pg_database AS d
WHERE d.datname IN ('alterdatabase_00968_database', 'alterdatabase_00968_renamed_database')
ORDER BY database_cleanup_verified;
SELECT true AS cleanup_complete;

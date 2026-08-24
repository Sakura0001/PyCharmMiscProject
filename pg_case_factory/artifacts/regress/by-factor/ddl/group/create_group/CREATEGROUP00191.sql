-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE GROUP privilege_level=non_createrole
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEGROUP00191
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/create_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/create_group.yaml
-- primary_obligation_id: CGP-EXT|00191|error_assertion|drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP GROUP IF EXISTS creategroup_00191_grp CASCADE;
DROP ROLE IF EXISTS creategroup_00191_grp CASCADE;
DROP ROLE IF EXISTS creategroup_00191_ref CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS creategroup_00191_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE creategroup_00191_actor LOGIN NOSUPERUSER NOCREATEROLE;
CREATE GROUP creategroup_00191_grp;
SET ROLE creategroup_00191_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE GROUP。
-- primary-target-begin
CREATE GROUP creategroup_00191_grp WITH LOGIN, PASSWORD 'pw';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS creategroup_00191_grp;
DROP ROLE IF EXISTS creategroup_00191_ref;
DROP OWNED BY creategroup_00191_actor CASCADE;
DROP ROLE IF EXISTS creategroup_00191_actor;
SELECT 1 AS residual_check_no_objects;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP GROUP privilege_level=non_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPGROUP00060
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/drop_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/drop_group.yaml
-- primary_obligation_id: DROPGROUP-EXT|00060|drop_group|notice_assertion|recreate_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP GROUP IF EXISTS dropgroup_00060_grp;
DROP OWNED BY dropgroup_00060_actor;
DROP ROLE IF EXISTS dropgroup_00060_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 group(role) 和因子专用夹具。
CREATE ROLE dropgroup_00060_actor LOGIN NOSUPERUSER NOCREATEROLE;
CREATE GROUP dropgroup_00060_grp;
SET ROLE dropgroup_00060_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP GROUP。
-- primary-target-begin
DROP GROUP dropgroup_00060_grp;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS group_present FROM pg_catalog.pg_roles WHERE rolname = 'dropgroup_00060_grp' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP GROUP IF EXISTS dropgroup_00060_grp;
DROP OWNED BY dropgroup_00060_actor;
DROP ROLE IF EXISTS dropgroup_00060_actor;

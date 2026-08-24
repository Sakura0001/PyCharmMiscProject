-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE GROUP target_form=create_group_with_options
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEGROUP00274
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/create_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/create_group.yaml
-- primary_obligation_id: CGP-EXT|00274|pg_authid_catalog_query|drop_group
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP GROUP IF EXISTS creategroup_00274_grp CASCADE;
DROP ROLE IF EXISTS creategroup_00274_grp CASCADE;
DROP ROLE IF EXISTS creategroup_00274_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE GROUP。
-- primary-target-begin
CREATE GROUP creategroup_00274_grp WITH LOGIN, ENCRYPTED PASSWORD 'pw';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS group_state FROM pg_catalog.pg_authid WHERE rolname = 'creategroup_00274_grp' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP GROUP IF EXISTS creategroup_00274_grp;
DROP ROLE IF EXISTS creategroup_00274_ref;
SELECT 1 AS residual_check_no_objects;

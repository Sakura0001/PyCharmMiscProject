-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE GROUP group_name_shape=quoted_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEGROUP00022
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/create_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/create_group.yaml
-- primary_obligation_id: CGP-SFV|sfv-aca6f8b8e16b98c1ea0cd4a8|create_group_with_options
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP GROUP IF EXISTS "creategroup_00022_qgrp" CASCADE;
DROP ROLE IF EXISTS "creategroup_00022_qgrp" CASCADE;
DROP ROLE IF EXISTS creategroup_00022_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE GROUP。
-- primary-target-begin
CREATE GROUP "creategroup_00022_qgrp" NOSUPERUSER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS group_state FROM pg_catalog.pg_authid WHERE rolname = 'creategroup_00022_qgrp' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP GROUP IF EXISTS "creategroup_00022_qgrp";
DROP ROLE IF EXISTS creategroup_00022_ref;
SELECT 1 AS residual_check_no_objects;

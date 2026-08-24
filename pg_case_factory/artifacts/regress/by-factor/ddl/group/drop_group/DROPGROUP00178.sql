-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP GROUP object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPGROUP00178
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/drop_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/drop_group.yaml
-- primary_obligation_id: DROPGROUP-EXT|00178|drop_group|notice_assertion|cleanup_referenced_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP GROUP IF EXISTS dropgroup_00178_grp;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 group(role) 和因子专用夹具。
CREATE GROUP dropgroup_00178_grp;
-- 3. 执行唯一获得覆盖信用的 DROP GROUP。
-- primary-target-begin
DROP GROUP IF EXISTS dropgroup_00178_grp;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS group_absent FROM pg_catalog.pg_roles WHERE rolname = 'dropgroup_00178_grp' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP GROUP IF EXISTS dropgroup_00178_grp;

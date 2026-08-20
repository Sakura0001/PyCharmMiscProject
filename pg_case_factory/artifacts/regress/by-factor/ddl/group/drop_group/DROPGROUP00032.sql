-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP GROUP role_still_referenced=has_references
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPGROUP00032
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/drop_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/drop_group.yaml
-- primary_obligation_id: DROPGROUP-SFV|sfv-2e1ebe4e8b212703660254ae|drop_group
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropgroup_00032_t CASCADE;
DROP GROUP IF EXISTS dropgroup_00032_grp;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 group(role) 和因子专用夹具。
CREATE GROUP dropgroup_00032_grp;
CREATE TABLE dropgroup_00032_t (c integer);
ALTER TABLE dropgroup_00032_t OWNER TO dropgroup_00032_grp;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP GROUP。
-- primary-target-begin
DROP GROUP dropgroup_00032_grp;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS group_present FROM pg_catalog.pg_roles WHERE rolname = 'dropgroup_00032_grp' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP GROUP IF EXISTS dropgroup_00032_grp;
DROP TABLE IF EXISTS dropgroup_00032_t CASCADE;

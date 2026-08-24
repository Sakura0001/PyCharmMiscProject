-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER VIEW target_action=drop_default
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERVIEW00263
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/alter_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/alter_view.yaml
-- primary_obligation_id: AVIEW-EXT|00263|select_from_view|revert_alter
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS alterview_00263_view;
DROP OWNED BY alterview_00263_actor CASCADE;
DROP ROLE IF EXISTS alterview_00263_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterview_00263_actor LOGIN;
SET ROLE alterview_00263_actor;
CREATE VIEW alterview_00263_view AS SELECT 1 AS alterview_00263_col, 2 AS alterview_00263_col2;
-- 3. 执行唯一获得覆盖信用的 ALTER VIEW。
-- primary-target-begin
ALTER VIEW IF EXISTS alterview_00263_view ALTER "alterview_00263_col" DROP DEFAULT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 1 AS view_probe FROM alterview_00263_view LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS alterview_00263_view;
DROP OWNED BY alterview_00263_actor CASCADE;
DROP ROLE IF EXISTS alterview_00263_actor;

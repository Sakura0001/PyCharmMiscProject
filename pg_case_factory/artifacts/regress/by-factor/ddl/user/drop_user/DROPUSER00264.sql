-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP USER object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPUSER00264
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/drop_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/drop_user.yaml
-- primary_obligation_id: DROPUSER-EXT|00264|drop_user|notice_assertion|terminate_sessions
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS dropuser_00264_norole;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
-- 3. 执行唯一获得覆盖信用的 DROP USER。
-- primary-target-begin
DROP USER IF EXISTS dropuser_00264_norole;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS user_absent FROM pg_catalog.pg_roles WHERE rolname = 'dropuser_00264_norole' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS dropuser_00264_norole;

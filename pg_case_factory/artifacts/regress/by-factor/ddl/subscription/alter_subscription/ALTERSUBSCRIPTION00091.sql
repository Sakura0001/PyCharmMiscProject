-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SUBSCRIPTION conninfo_string_shape=invalid_conninfo
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSUBSCRIPTION00091
-- source_md: skills/pg-sql-generation/references/statements/ddl/subscription/alter_subscription.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/subscription/alter_subscription.yaml
-- primary_obligation_id: ASUB-EXT|00091|error_assertion|drop_subscription
-- expected_outcome: expected_failure
-- expected_sqlstate: 08001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SUBSCRIPTION IF EXISTS "alter_subscription_00091_Mixed Sub";
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SUBSCRIPTION "alter_subscription_00091_Mixed Sub" CONNECTION 'host=localhost port=5432 dbname=pgcf' PUBLICATION alter_subscription_00091_pub WITH (enabled = false, create_slot = false, copy_data = false, slot_name = NONE);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SUBSCRIPTION。
-- primary-target-begin
ALTER SUBSCRIPTION "alter_subscription_00091_Mixed Sub" CONNECTION 'invalid_conninfo_string';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '08001' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP SUBSCRIPTION IF EXISTS "alter_subscription_00091_Mixed Sub";

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SUBSCRIPTION executor_privilege=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSUBSCRIPTION00195
-- source_md: skills/pg-sql-generation/references/statements/ddl/subscription/alter_subscription.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/subscription/alter_subscription.yaml
-- primary_obligation_id: ASUB-EXT|00195|error_assertion|drop_subscription
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SUBSCRIPTION IF EXISTS "alter_subscription_00195_Mixed Sub";
DROP OWNED BY alter_subscription_00195_actor CASCADE;
DROP ROLE IF EXISTS alter_subscription_00195_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alter_subscription_00195_actor LOGIN NOSUPERUSER;
CREATE SUBSCRIPTION "alter_subscription_00195_Mixed Sub" CONNECTION 'host=localhost port=5432 dbname=pgcf' PUBLICATION alter_subscription_00195_pub WITH (enabled = false, create_slot = false, copy_data = false, slot_name = NONE);
SET ROLE alter_subscription_00195_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SUBSCRIPTION。
-- primary-target-begin
ALTER SUBSCRIPTION "alter_subscription_00195_Mixed Sub" ADD PUBLICATION "alter_subscription_00195_Mixed Pub";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SUBSCRIPTION IF EXISTS "alter_subscription_00195_Mixed Sub";
DROP OWNED BY alter_subscription_00195_actor CASCADE;
DROP ROLE IF EXISTS alter_subscription_00195_actor;

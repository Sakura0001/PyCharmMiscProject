-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SUBSCRIPTION target_form=create_subscription
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESUBSCRIPTION01084
-- source_md: skills/pg-sql-generation/references/statements/ddl/subscription/create_subscription.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/subscription/create_subscription.yaml
-- primary_obligation_id: CSUB-EXT|01084|pg_subscription_catalog|drop_subscription|slot_copy
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SUBSCRIPTION IF EXISTS "createsubscription_01084_User";
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SUBSCRIPTION "createsubscription_01084_User" CONNECTION 'host=127.0.0.1 port=55999 user=pgcf_superuser dbname=pgcf_cop' PUBLICATION createsubscription_01084_pub WITH (enabled = false, create_slot = false, copy_data = false, slot_name = NONE);
-- 3. 执行唯一获得覆盖信用的 CREATE SUBSCRIPTION。
-- primary-target-begin
CREATE SUBSCRIPTION "createsubscription_01084_User" CONNECTION 'not_a_valid_conninfo' PUBLICATION createsubscription_01084_pub1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS subscription_state FROM pg_catalog.pg_subscription WHERE subname = 'createsubscription_01084_User' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SUBSCRIPTION IF EXISTS "createsubscription_01084_User";

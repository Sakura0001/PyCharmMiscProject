-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP SUBSCRIPTION privilege_context=non_superuser_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSUBSCRIPTION00582
-- source_md: skills/pg-sql-generation/references/statements/ddl/subscription/drop_subscription.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/subscription/drop_subscription.yaml
-- primary_obligation_id: DROPSUBSCRIPTION-EXT|00582|drop_subscription|error_assertion|drop_subscription_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SUBSCRIPTION IF EXISTS dropsubscription_00582_nosub CASCADE;
DROP OWNED BY dropsubscription_00582_actor;
DROP ROLE IF EXISTS dropsubscription_00582_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地订阅和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE dropsubscription_00582_actor LOGIN NOSUPERUSER;
SELECT 1 AS target_subscription_intentionally_absent;
SET ROLE dropsubscription_00582_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP SUBSCRIPTION。
-- primary-target-begin
DROP SUBSCRIPTION IF EXISTS dropsubscription_00582_nosub;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS subscription_absent FROM pg_catalog.pg_subscription WHERE subname = 'dropsubscription_00582_nosub' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SUBSCRIPTION IF EXISTS dropsubscription_00582_nosub CASCADE;
DROP OWNED BY dropsubscription_00582_actor;
DROP ROLE IF EXISTS dropsubscription_00582_actor;

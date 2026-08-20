-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP SUBSCRIPTION target_action=drop_subscription
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSUBSCRIPTION00001
-- source_md: skills/pg-sql-generation/references/statements/ddl/subscription/drop_subscription.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/subscription/drop_subscription.yaml
-- primary_obligation_id: DROPSUBSCRIPTION-GRM|branch_1|drop_subscription|target_action|drop_subscription
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SUBSCRIPTION IF EXISTS dropsubscription_00001_sub CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地订阅和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE SUBSCRIPTION dropsubscription_00001_sub CONNECTION 'host=127.0.0.1 port=1 dbname=dummy' PUBLICATION dummy_pub WITH (connect = false);
-- 3. 执行唯一获得覆盖信用的 DROP SUBSCRIPTION。
-- primary-target-begin
DROP SUBSCRIPTION dropsubscription_00001_sub;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS subscription_absent FROM pg_catalog.pg_subscription WHERE subname = 'dropsubscription_00001_sub' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SUBSCRIPTION IF EXISTS dropsubscription_00001_sub CASCADE;

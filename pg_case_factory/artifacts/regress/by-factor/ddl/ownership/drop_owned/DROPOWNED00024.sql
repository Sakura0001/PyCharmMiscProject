-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OWNED privilege_insufficient=non_superuser_dropping_other_role_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOWNED00024
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/drop_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/drop_owned.yaml
-- primary_obligation_id: DROPOWNED-SFV|sfv-04ceca3c5595a34734fd5ed4|drop_owned
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OWNED BY dropowned_00024_executor;
DROP ROLE IF EXISTS dropowned_00024_executor;
DROP OWNED BY dropowned_00024_actor;
DROP ROLE IF EXISTS dropowned_00024_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE dropowned_00024_actor LOGIN;
CREATE ROLE dropowned_00024_executor LOGIN NOSUPERUSER;
SET ROLE dropowned_00024_executor;
-- 3. 执行唯一获得覆盖信用的 DROP OWNED。
-- primary-target-begin
DROP OWNED BY dropowned_00024_actor;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS objects_absent FROM pg_catalog.pg_class WHERE relname = 'dropowned_00024_t' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY dropowned_00024_executor;
DROP ROLE IF EXISTS dropowned_00024_executor;
DROP OWNED BY dropowned_00024_actor;
DROP ROLE IF EXISTS dropowned_00024_actor;

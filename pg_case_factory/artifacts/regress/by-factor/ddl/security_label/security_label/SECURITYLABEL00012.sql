-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SECURITY LABEL ON executor_privilege=non_superuser_no_provider_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SECURITYLABEL00012
-- source_md: skills/pg-sql-generation/references/statements/ddl/security_label/security_label.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/security_label/security_label.yaml
-- primary_obligation_id: SECURITYLABEL-SFV|sfv-7d174dc1884d22e243c487d0|table
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS securitylabel_00012_tbl CASCADE;
DROP OWNED BY securitylabel_00012_actor CASCADE;
DROP ROLE IF EXISTS securitylabel_00012_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE securitylabel_00012_actor LOGIN NOSUPERUSER;
CREATE TABLE securitylabel_00012_tbl (id int);
SET ROLE securitylabel_00012_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 SECURITY LABEL。
-- primary-target-begin
SECURITY LABEL ON TABLE securitylabel_00012_tbl IS 'classification';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS label_count FROM pg_catalog.pg_seclabels WHERE provider = 'seclabel' AND label = 'classification' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
SECURITY LABEL ON TABLE securitylabel_00012_tbl IS NULL;
DROP OWNED BY securitylabel_00012_actor CASCADE;
DROP ROLE IF EXISTS securitylabel_00012_actor;
DROP TABLE IF EXISTS securitylabel_00012_tbl;

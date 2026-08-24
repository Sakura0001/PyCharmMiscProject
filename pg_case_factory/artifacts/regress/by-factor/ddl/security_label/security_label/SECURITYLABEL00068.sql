-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SECURITY LABEL ON statement_branch=branch_on_foreign_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SECURITYLABEL00068
-- source_md: skills/pg-sql-generation/references/statements/ddl/security_label/security_label.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/security_label/security_label.yaml
-- primary_obligation_id: SECURITYLABEL-SFV|sfv-6c951e7b428c044e4414c9a1|foreign_table
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS securitylabel_00068_ft;
DROP SERVER IF EXISTS securitylabel_00068_srv;
DROP FOREIGN DATA WRAPPER IF EXISTS securitylabel_00068_fdw;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER securitylabel_00068_fdw;
CREATE SERVER securitylabel_00068_srv FOREIGN DATA WRAPPER securitylabel_00068_fdw;
CREATE FOREIGN TABLE securitylabel_00068_ft (id int) SERVER securitylabel_00068_srv;
-- 3. 执行唯一获得覆盖信用的 SECURITY LABEL。
-- primary-target-begin
SECURITY LABEL ON FOREIGN TABLE securitylabel_00068_ft IS 'classification';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS label_count FROM pg_catalog.pg_seclabels WHERE provider = 'seclabel' AND label = 'classification' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
SECURITY LABEL ON FOREIGN TABLE securitylabel_00068_ft IS NULL;
DROP FOREIGN TABLE IF EXISTS securitylabel_00068_ft;
DROP SERVER IF EXISTS securitylabel_00068_srv;
DROP FOREIGN DATA WRAPPER IF EXISTS securitylabel_00068_fdw;

-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SECURITY LABEL ON object_type=table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SECURITYLABEL00160
-- source_md: skills/pg-sql-generation/references/statements/ddl/security_label/security_label.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/security_label/security_label.yaml
-- primary_obligation_id: SECURITYLABEL-EXT|00160|pg_seclabel_catalog_query|drop_object
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS securitylabel_00160_tbl CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE securitylabel_00160_tbl (id int);
-- 3. 执行唯一获得覆盖信用的 SECURITY LABEL。
-- primary-target-begin
SECURITY LABEL ON TABLE securitylabel_00160_tbl IS NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS label_count FROM pg_catalog.pg_seclabels WHERE provider = 'seclabel' AND label = '' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS securitylabel_00160_tbl;

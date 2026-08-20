-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP DOMAIN nonexistent_domain=domain_missing_without_if_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPDOMAIN00381
-- source_md: skills/pg-sql-generation/references/statements/ddl/domain/drop_domain.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/domain/drop_domain.yaml
-- primary_obligation_id: DROPDOMAIN-EXT|00381|drop_domain|error_assertion|drop_domain
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP DOMAIN IF EXISTS dropdomain_00381_dom CASCADE;
DROP DOMAIN IF EXISTS dropdomain_00381_dom2 CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地域和因子专用夹具。
SELECT 1 AS target_domain_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP DOMAIN。
-- primary-target-begin
DROP DOMAIN dropdomain_00381_dom, dropdomain_00381_dom2 RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS domain_absent FROM pg_catalog.pg_type WHERE typname = 'dropdomain_00381_dom' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP DOMAIN IF EXISTS dropdomain_00381_dom CASCADE;
DROP DOMAIN IF EXISTS dropdomain_00381_dom2 CASCADE;

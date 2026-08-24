-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP DOMAIN privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPDOMAIN00236
-- source_md: skills/pg-sql-generation/references/statements/ddl/domain/drop_domain.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/domain/drop_domain.yaml
-- primary_obligation_id: DROPDOMAIN-EXT|00236|drop_domain|error_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP DOMAIN IF EXISTS dropdomain_00236_dom CASCADE;
DROP DOMAIN IF EXISTS dropdomain_00236_dom2 CASCADE;
DROP ROLE IF EXISTS dropdomain_00236_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地域和因子专用夹具。
CREATE ROLE dropdomain_00236_actor LOGIN NOSUPERUSER;
CREATE DOMAIN dropdomain_00236_dom AS integer NOT NULL;
CREATE DOMAIN dropdomain_00236_dom2 AS integer NOT NULL;
SET ROLE dropdomain_00236_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP DOMAIN。
-- primary-target-begin
DROP DOMAIN IF EXISTS dropdomain_00236_dom, dropdomain_00236_dom2 CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS domain_present FROM pg_catalog.pg_type WHERE typname = 'dropdomain_00236_dom' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP DOMAIN IF EXISTS dropdomain_00236_dom CASCADE;
DROP DOMAIN IF EXISTS dropdomain_00236_dom2 CASCADE;
DROP OWNED BY dropdomain_00236_actor;
DROP ROLE IF EXISTS dropdomain_00236_actor;

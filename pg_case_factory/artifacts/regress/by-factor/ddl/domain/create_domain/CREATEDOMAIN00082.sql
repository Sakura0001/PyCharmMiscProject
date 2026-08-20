-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE DOMAIN privilege_level=non_owner_no_create
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEDOMAIN00082
-- source_md: skills/pg-sql-generation/references/statements/ddl/domain/create_domain.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/domain/create_domain.yaml
-- primary_obligation_id: CD-SFV|sfv-0d0caa94997f381618b957ec|create_domain
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OWNED BY createdomain_00082_actor CASCADE;
DROP ROLE IF EXISTS createdomain_00082_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createdomain_00082_actor LOGIN NOSUPERUSER;
SET ROLE createdomain_00082_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE DOMAIN。
-- primary-target-begin
CREATE DOMAIN createdomain_00082_dom AS integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS domain_state FROM pg_catalog.pg_type WHERE typname = 'createdomain_00082_dom' AND typtype = 'd' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY createdomain_00082_actor CASCADE;
DROP ROLE IF EXISTS createdomain_00082_actor;

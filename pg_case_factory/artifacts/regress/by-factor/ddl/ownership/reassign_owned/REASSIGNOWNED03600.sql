-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : REASSIGN OWNED owned_objects_state=owns_tables
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REASSIGNOWNED03600
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/reassign_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/reassign_owned.yaml
-- primary_obligation_id: REASSIGNOWNED-EXT|03600|reassign_owned|pg_roles_catalog_query|drop_role_cascade
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reassignowned_03600_t CASCADE;
DROP OWNED BY reassignowned_03600_old;
DROP OWNED BY reassignowned_03600_new;
DROP ROLE IF EXISTS reassignowned_03600_old;
DROP ROLE IF EXISTS reassignowned_03600_new;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE reassignowned_03600_old LOGIN;
CREATE ROLE reassignowned_03600_new LOGIN;
CREATE TABLE reassignowned_03600_t (c integer);
ALTER TABLE reassignowned_03600_t OWNER TO reassignowned_03600_old;
SET ROLE reassignowned_03600_new;
-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。
-- primary-target-begin
REASSIGN OWNED BY reassignowned_03600_old TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_present FROM pg_catalog.pg_roles WHERE rolname = 'reassignowned_03600_old' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY reassignowned_03600_old;
DROP OWNED BY reassignowned_03600_new;
DROP ROLE IF EXISTS reassignowned_03600_old;
DROP ROLE IF EXISTS reassignowned_03600_new;
DROP TABLE IF EXISTS reassignowned_03600_t CASCADE;

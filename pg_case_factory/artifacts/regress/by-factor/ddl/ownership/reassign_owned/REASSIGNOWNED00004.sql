-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : REASSIGN OWNED cleanup_mode=reassign_owned_then_drop_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REASSIGNOWNED00004
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/reassign_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/reassign_owned.yaml
-- primary_obligation_id: REASSIGNOWNED-SFV|sfv-b9c1615dd81c7e61f0c3f82a|reassign_owned
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reassignowned_00004_t CASCADE;
DROP OWNED BY reassignowned_00004_old;
DROP OWNED BY reassignowned_00004_new;
DROP ROLE IF EXISTS reassignowned_00004_old;
DROP ROLE IF EXISTS reassignowned_00004_new;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE reassignowned_00004_old LOGIN;
CREATE ROLE reassignowned_00004_new LOGIN;
CREATE TABLE reassignowned_00004_t (c integer);
ALTER TABLE reassignowned_00004_t OWNER TO reassignowned_00004_old;
-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。
-- primary-target-begin
REASSIGN OWNED BY reassignowned_00004_old TO reassignowned_00004_new;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS ownership_transferred FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_roles AS r ON c.relowner = r.oid WHERE c.relname = 'reassignowned_00004_t' AND r.rolname = 'reassignowned_00004_new' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OWNED BY reassignowned_00004_old;
DROP OWNED BY reassignowned_00004_new;
DROP ROLE IF EXISTS reassignowned_00004_old;
DROP ROLE IF EXISTS reassignowned_00004_new;
DROP TABLE IF EXISTS reassignowned_00004_t CASCADE;

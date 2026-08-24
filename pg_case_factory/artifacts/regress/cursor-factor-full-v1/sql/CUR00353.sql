-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 FETCH with statement_branch=branch_1, expected_status=success, cursor_state=declared_open, direction_shape=relative, hold_scroll_shape=with_hold, cursor_name_shape=plain_identifier, query_shape=simple_select, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=none, position_boundary=middle, verification_mode=effect_query, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor cursor_state=declared_open
-- factor direction_shape=relative
-- factor hold_scroll_shape=with_hold
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=simple_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=middle
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00353_table;
CREATE TABLE cur_00353_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00353_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE cur_00353_cursor CURSOR WITH HOLD FOR SELECT id, payload FROM cur_00353_table ORDER BY id;
FETCH RELATIVE 1 FROM cur_00353_cursor;
SELECT count(*) AS source_rows FROM cur_00353_table;
SELECT count(*) AS cursor_effect_rows FROM cur_00353_table;
ROLLBACK;
DROP TABLE IF EXISTS cur_00353_table;

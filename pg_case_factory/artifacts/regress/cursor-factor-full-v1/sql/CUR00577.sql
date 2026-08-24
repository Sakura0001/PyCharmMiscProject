-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 MOVE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=all, hold_scroll_shape=no_scroll, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=inside_transaction, dependency_state=missing_dependency, invalid_combination=object_type_mismatch, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=reset_state
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=all
-- factor hold_scroll_shape=no_scroll
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=object_type_mismatch
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS cur_00577_table;
CREATE TABLE cur_00577_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00577_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE cur_00577_cursor NO SCROLL CURSOR FOR SELECT id FROM cur_00577_missing_table ORDER BY id;
MOVE ALL FROM cur_00577_table;
SELECT 1 AS failure_boundary;
SELECT id, payload FROM cur_00577_table ORDER BY id;
ROLLBACK;
RESET ALL;
DROP TABLE IF EXISTS cur_00577_table;

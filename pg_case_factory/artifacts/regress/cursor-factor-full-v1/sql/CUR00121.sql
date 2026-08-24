-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 CLOSE with statement_branch=branch_1, expected_status=failure, cursor_state=closed_cursor, direction_shape=absolute, hold_scroll_shape=without_hold, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=inside_transaction, dependency_state=missing_dependency, invalid_combination=object_type_mismatch, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=reset_state
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=closed_cursor
-- factor direction_shape=absolute
-- factor hold_scroll_shape=without_hold
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=object_type_mismatch
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS cur_00121_table;
CREATE TABLE cur_00121_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00121_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE cur_00121_cursor CURSOR WITHOUT HOLD FOR SELECT id FROM cur_00121_missing_table ORDER BY id;
CLOSE cur_00121_cursor;
CLOSE cur_00121_table;
SELECT id, payload FROM cur_00121_table ORDER BY id;
ROLLBACK;
RESET ALL;
DROP TABLE IF EXISTS cur_00121_table;

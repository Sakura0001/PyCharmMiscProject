-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 CLOSE with statement_branch=branch_1, expected_status=failure, cursor_state=missing_cursor, direction_shape=absolute, hold_scroll_shape=no_scroll, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=outside_transaction, dependency_state=missing_dependency, invalid_combination=syntax_valid_semantic_error, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=missing_cursor
-- factor direction_shape=absolute
-- factor hold_scroll_shape=no_scroll
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=outside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=syntax_valid_semantic_error
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00093_table;
CREATE TABLE cur_00093_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00093_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
CLOSE cur_00093_missing_cursor;
SELECT id, payload FROM cur_00093_table ORDER BY id;
COMMIT;
DROP TABLE IF EXISTS cur_00093_table;

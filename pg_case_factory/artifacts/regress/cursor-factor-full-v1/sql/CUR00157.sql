-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 CLOSE with statement_branch=branch_1, expected_status=failure, cursor_state=with_hold_after_commit, direction_shape=relative, hold_scroll_shape=scroll, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=inside_transaction, dependency_state=missing_dependency, invalid_combination=object_type_mismatch, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=reset_state
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=with_hold_after_commit
-- factor direction_shape=relative
-- factor hold_scroll_shape=scroll
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=object_type_mismatch
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS cur_00157_table;
CREATE TABLE cur_00157_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00157_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE cur_00157_cursor SCROLL CURSOR WITH HOLD FOR SELECT id FROM cur_00157_missing_table ORDER BY id;
CLOSE cur_00157_table;
SELECT id, payload FROM cur_00157_table ORDER BY id;
ROLLBACK;
RESET ALL;
DROP TABLE IF EXISTS cur_00157_table;

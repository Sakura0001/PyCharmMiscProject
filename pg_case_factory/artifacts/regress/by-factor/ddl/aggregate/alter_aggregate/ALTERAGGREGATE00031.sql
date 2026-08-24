-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify ALTER AGGREGATE RENAME for s04_ordered_set, quoted_identifier, plain_identifier
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERAGGREGATE00031
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/alter_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/alter_aggregate.yaml
-- factor_values: statement_branch=branch_rename, aggregate_signature=ordered_set_signature, aggregate_form=ordered_set, expected_status=success, target_state=new_name_available, aggregate_name_shape=quoted_identifier, new_name_shape=plain_identifier, privilege_level=superuser, verification_mode=pg_aggregate_actual_execution, cleanup_mode=DROP_AGGREGATE
-- derived_axes: aggregate_kind=o, aggregate_name_shape=quoted_identifier, branch=rename, cleanup_mode=DROP_AGGREGATE, direct_arg_count=1, expected_sqlstate=00000, fixture_kind=ordered, flat_arg_count=2, new_name_shape=plain_identifier, signature_id=s04_ordered_set, signature_key=ordered_set_signature, target_signature=double precision ORDER BY integer, verification_mode=pg_aggregate_actual_execution
-- combination_strategy: full conditional Cartesian S14 signatures × 3 aggregate-name shapes × 3 rename-target shapes
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000, stable aggregate identity, new name only, and unchanged execution result
-- 1. 幂等清理本编号对象；角色、schema 和关系均只属于当前文件。
DROP TABLE IF EXISTS public.alteraggregate_00031_data CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS alteraggregate_00031_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00031_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00031_actor, alteraggregate_00031_intruder, alteraggregate_00031_old_owner, alteraggregate_00031_new_owner;
CREATE SCHEMA alteraggregate_00031_src;
SET search_path TO alteraggregate_00031_src, pg_catalog;
CREATE TABLE public.alteraggregate_00031_data (
    id integer PRIMARY KEY,
    group_key text NOT NULL,
    input_one integer NOT NULL CHECK (input_one > 0),
    input_two integer NOT NULL CHECK (input_two > 0),
    note text NOT NULL CHECK (length(note) > 0),
    CONSTRAINT alteraggregate_00031_data_unique UNIQUE (group_key, id)
);
INSERT INTO public.alteraggregate_00031_data(id, group_key, input_one, input_two, note) VALUES
    (1, 'g1', 1, 10, 'a'),
    (2, 'g1', 2, 20, 'bb'),
    (3, 'g2', 3, 30, 'ccc');

-- 2. 创建完整 support function 与用户自定义聚合；不修改任何内置聚合。
CREATE FUNCTION alteraggregate_00031_src.alteraggregate_00031_step(state bigint, ordered_value integer) RETURNS bigint
LANGUAGE sql IMMUTABLE
AS 'SELECT state + COALESCE(ordered_value, 0)';
CREATE FUNCTION alteraggregate_00031_src.alteraggregate_00031_final(state bigint, direct_value double precision) RETURNS double precision
LANGUAGE sql IMMUTABLE
AS 'SELECT state::double precision + direct_value';
CREATE AGGREGATE alteraggregate_00031_src."alteraggregate_00031_Aggregate Name"(direct_value double precision ORDER BY ordered_value integer) (
    SFUNC = alteraggregate_00031_src.alteraggregate_00031_step,
    STYPE = bigint,
    FINALFUNC = alteraggregate_00031_src.alteraggregate_00031_final,
    INITCOND = '0'
);
SELECT p.oid::text AS before_oid
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'alteraggregate_00031_src'
  AND p.proname = 'alteraggregate_00031_Aggregate Name'
  AND p.prokind = 'a'
ORDER BY p.oid
\gset

-- 3. 建立本格唯一的目标状态、权限或冲突前置条件。
SELECT true AS target_context_ready;

-- 4. 执行唯一目标 ALTER AGGREGATE；expected SQLSTATE 00000。
\set ON_ERROR_STOP off
ALTER AGGREGATE "alteraggregate_00031_Aggregate Name"(double precision ORDER BY integer) RENAME TO alteraggregate_00031_renamed;
\echo target_sqlstate :SQLSTATE
SELECT :'SQLSTATE' = '00000' AS target_sqlstate_matches;
\set ON_ERROR_STOP on
RESET ROLE;

-- 5. 用 schema、prokind、aggkind、direct 参数数、arity 和保存的 OID 验证结果。
SELECT
    count(*) = 1 AS target_aggregate_present,
    COALESCE(bool_and(p.oid::text = :'before_oid'), false) AS target_aggregate_oid_stable,
    COALESCE(bool_and(a.aggkind = 'o'), false) AS target_aggregate_kind_stable,
    COALESCE(bool_and(a.aggnumdirectargs = 1), false) AS target_aggregate_direct_count_stable,
    COALESCE(bool_and(p.pronargs = 2), false) AS target_aggregate_arity_stable
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
JOIN pg_catalog.pg_aggregate AS a ON a.aggfnoid = p.oid
WHERE n.nspname = 'alteraggregate_00031_src'
  AND p.proname = 'alteraggregate_00031_renamed'
  AND p.prokind = 'a'
ORDER BY target_aggregate_present, target_aggregate_oid_stable, target_aggregate_kind_stable, target_aggregate_direct_count_stable, target_aggregate_arity_stable;

-- 6. 成功主积执行修改后的聚合；失败格只做独立会话可用性和不变性锚定。
SELECT alteraggregate_00031_src."alteraggregate_00031_renamed"(10.0::double precision) WITHIN GROUP (ORDER BY input_one) = 16.0::double precision AS aggregate_execution_matches
FROM public.alteraggregate_00031_data;

-- 7. 按实际最终 identity 反向清理 aggregate、support functions、schema、role 与输入表。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP AGGREGATE alteraggregate_00031_src."alteraggregate_00031_renamed"(direct_value double precision ORDER BY ordered_value integer);
DROP SCHEMA IF EXISTS alteraggregate_00031_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00031_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00031_actor, alteraggregate_00031_intruder, alteraggregate_00031_old_owner, alteraggregate_00031_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;
DROP TABLE IF EXISTS public.alteraggregate_00031_data CASCADE;

# Internal MySQL 8.0 Common-Factor Workbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat 815-row workbook with an auditable model that separates atomic feature points from reusable factors and expands every applicable factor value into executable OFAT cases, plus P0 interaction coverage.

**Architecture:** JavaScript data builders normalize the four existing JSON inventories into six typed datasets: audit records, common factors, special factors, feature points, constraints, and Oracle packages. A deterministic expansion engine generates baseline and OFAT cases, the 64 ordered two-level partition combinations, INSTANT-count scenarios, and bounded P0 directed combinations. A single `@oai/artifact-tool` builder writes and verifies the final workbook.

**Tech Stack:** Bundled Node.js, JavaScript ES modules, JSON intermediates, `@oai/artifact-tool`, shell/JQ for read-only validation.

---

### Task 1: Establish the v2 data contract and audit map

**Files:**
- Create: `.codex_tmp/online_modify_v2/model.mjs`
- Create: `.codex_tmp/online_modify_v2/audit.mjs`
- Create: `.codex_tmp/online_modify_v2/self_test.mjs`
- Read: `.codex_tmp/online_modify/{core_points,rds_supplement_points,enhancement_points,unique_points}.json`

- [ ] **Step 1: Write contract assertions in `self_test.mjs`**

Assert that feature points have one behavior, factors have stable IDs/defaults, constraints have predicates and reasons, and every old ID receives one classification.

- [ ] **Step 2: Run the assertions and confirm they fail before model files exist**

Run: `node .codex_tmp/online_modify_v2/self_test.mjs`

Expected: nonzero exit with a missing model/audit module error.

- [ ] **Step 3: Implement the record constructors and old-ID classification ranges**

Use classifications `FUNCTION_POINT`, `COMMON_FACTOR`, `SPECIAL_FACTOR`, `SCENARIO`, `ORACLE`, `CONSTRAINT`, `NON_TARGET_CONTROL`, and `SUMMARY`. Preserve the old record text and map every one of the 815 IDs to its new destination or exclusion reason.

- [ ] **Step 4: Run contract tests**

Run: `node .codex_tmp/online_modify_v2/self_test.mjs`

Expected: 815 audited source records, zero missing IDs, zero duplicate source IDs.

### Task 2: Build the common-factor and two-level partition dictionaries

**Files:**
- Create: `.codex_tmp/online_modify_v2/common_factors.mjs`
- Create: `.codex_tmp/online_modify_v2/partition_matrix.mjs`
- Modify: `.codex_tmp/online_modify_v2/self_test.mjs`

- [ ] **Step 1: Add failing tests for required factor dimensions**

Assert the presence of row format, tablespace, table width, target-column position, data scale, data profile, table history, concurrent DML, transaction/MDL, resource, failure, and replication dimensions.

- [ ] **Step 2: Add failing tests for partition and scale boundaries**

Assert exactly eight partition methods, exactly 64 unique ordered primary/subpartition pairs, and data scales containing 10M, 50M, 100M, 200M+, greater-than-buffer-pool, and at-least-10GB values.

- [ ] **Step 3: Implement the dictionaries**

Use the eight methods `RANGE`, `RANGE COLUMNS`, `LIST`, `LIST COLUMNS`, `HASH`, `LINEAR HASH`, `KEY`, and `LINEAR KEY`. Assign every value an execution tier, default flag, scope, applicability note, and observation focus.

- [ ] **Step 4: Verify dictionaries**

Run: `node .codex_tmp/online_modify_v2/self_test.mjs`

Expected: 64 ordered partition pairs, no duplicate factor/value IDs, and all mandatory large-data values present.

### Task 3: Normalize the atomic feature-point catalog

**Files:**
- Create: `.codex_tmp/online_modify_v2/feature_points.mjs`
- Create: `.codex_tmp/online_modify_v2/special_factors.mjs`
- Modify: `.codex_tmp/online_modify_v2/self_test.mjs`

- [ ] **Step 1: Add tests that reject background-only feature points**

Reject points whose only behavior is empty/small/large table, a row format, a tablespace, a workload, an Oracle, a failure injection, or a monitoring method.

- [ ] **Step 2: Normalize repeated type-edge rows**

Represent each source/target conversion once and move signedness, algorithm, lock, switch state, index role, and partition-key role into special factors where they alter semantics.

- [ ] **Step 3: Preserve all requested feature families**

Create atomic points for integer and string expansion, DECIMAL precision expansion, indexed virtual-generated-column expansion, unique-key temporary conflict behavior, explicit algorithm strictness, target-column limitations, multi-action atomicity, and INSTANT-count limits.

- [ ] **Step 4: Verify feature-point integrity**

Run: `node .codex_tmp/online_modify_v2/self_test.mjs`

Expected: every retained feature point has a single action, primary expectation, source level, and applicability signature; no semantic duplicates.

### Task 4: Implement constraints, Oracle packages, and observation derivation

**Files:**
- Create: `.codex_tmp/online_modify_v2/constraints.mjs`
- Create: `.codex_tmp/online_modify_v2/oracles.mjs`
- Create: `.codex_tmp/online_modify_v2/derive_expectation.mjs`
- Modify: `.codex_tmp/online_modify_v2/self_test.mjs`

- [ ] **Step 1: Add tests for invalid combinations and derived expectations**

Cover empty-table/data-profile conflicts, invalid row-format/tablespace pairs, target index and partition-key restrictions, unique-key exclusions, `LOCK=SHARED` write waiting, large-data applicability, and INSTANT-limit behavior.

- [ ] **Step 2: Implement reusable Oracle packages**

Provide packages for algorithm path, MDL/lock, schema, data, index, partition, concurrency, resource, error, atomicity, replication, recovery, and INSTANT counter validation.

- [ ] **Step 3: Implement observation text generation**

Every case must receive nonempty `主要风险`, `重点观察`, `观察方法`, and `通过标准`. Combine the feature-point focus with factor-specific additions such as per-partition checks, row-log pressure, compressed-row I/O, billion-row resource peaks, or counter reset.

- [ ] **Step 4: Run derivation tests**

Run: `node .codex_tmp/online_modify_v2/self_test.mjs`

Expected: all fixture cases have deterministic algorithm/lock/result expectations and nonempty observations.

### Task 5: Generate baseline, OFAT, P0 interaction, and INSTANT-count cases

**Files:**
- Create: `.codex_tmp/online_modify_v2/expand_cases.mjs`
- Create: `.codex_tmp/online_modify_v2/generate_datasets.mjs`
- Modify: `.codex_tmp/online_modify_v2/self_test.mjs`
- Generate: `.codex_tmp/online_modify_v2/generated/*.json`

- [ ] **Step 1: Add coverage tests**

For every feature point, require one baseline case. For every `ALL_LEVELS` or allowed `CONSTRAINED` value, require at least one OFAT case or an explicit not-applicable audit row.

- [ ] **Step 2: Implement deterministic OFAT expansion**

Each row changes one factor value and materializes all other baseline columns. Assign stable IDs from feature-point ID, factor ID, and value ID.

- [ ] **Step 3: Generate the 64 partition variants**

For every partition-compatible feature point, emit all 64 ordered two-level partition combinations. For representative P0 points, add 64×10M and 64×100M directed cases plus key-role limitation variants.

- [ ] **Step 4: Generate P0 pairwise/directed cases**

Add bounded high-risk sets for row format×tablespace×row width, data scale×threads×transaction length, concurrency rate×online-log capacity×disk margin, charset×VARCHAR boundary×index type, row-log phase×conflict type×commit/rollback, and `LOCK=SHARED`×DML type×MDL queue.

- [ ] **Step 5: Generate INSTANT history cases**

Cover counts 0, 1, 2, 8, 16, 32, `INSTANT_LIMIT-1`, `INSTANT_LIMIT`, failed repeats, default-algorithm fallback/rejection, rebuild reset, one-column growth, multi-column rotation, mixed instant history, two-level partition history, and commit-boundary restart.

- [ ] **Step 6: Run full dataset tests**

Run: `node .codex_tmp/online_modify_v2/generate_datasets.mjs && node .codex_tmp/online_modify_v2/self_test.mjs --generated`

Expected: zero duplicate execution IDs, zero missing observation fields, all 64 partition pairs covered, all required large-data and INSTANT-limit scenarios covered, and no unexplained dropped source record.

### Task 6: Author the workbook

**Files:**
- Create: `.codex_tmp/online_modify_v2/build_workbook.mjs`
- Output: `outputs/online_modify_column_20260902/RDS_MySQL80_在线修改列类型_公共因子展开全集.xlsx`

- [ ] **Step 1: Load the bundled spreadsheet runtime**

Use `codex_app__load_workspace_dependencies`, create a local `node_modules` symlink, and run the spreadsheet operation marker exactly once immediately before authoring.

- [ ] **Step 2: Create the 15 specified worksheets**

Create `00_说明与统计` through `14_来源`, including the 64-pair partition sheet, separate OFAT and P0 interaction tables, INSTANT history, constraints, Oracle packages, and coverage audit.

- [ ] **Step 3: Apply workbook usability formatting**

Use tables and filters, freeze headers/key columns, fixed readable widths, wrapped text, priority/execution-tier/status validation, source URLs, and conditional formatting for P0, not-applicable, missing coverage, and failed status.

- [ ] **Step 4: Add formula-driven summary and coverage checks**

Derive counts and missing-coverage status from data sheets with bounded formulas. Split execution rows by feature domain if a sheet approaches 900,000 rows.

- [ ] **Step 5: Inspect, render, and export**

Inspect representative ranges and formula errors, render every sheet or a representative range from every sheet, repair clipping, and export the final workbook.

### Task 7: Independently verify the exported workbook

**Files:**
- Create: `.codex_tmp/online_modify_v2/verify_workbook.mjs`

- [ ] **Step 1: Re-import the exported XLSX**

Verify all expected sheets exist and key tables have their expected headers and nonzero data rows.

- [ ] **Step 2: Reconcile counts**

Confirm the workbook feature-point, factor-value, partition-pair, OFAT, P0-interaction, INSTANT-history, source-audit, and coverage totals match generated JSON.

- [ ] **Step 3: Validate coverage and content**

Require 64 unique partition pairs, mandatory 10M/50M/100M/200M+/buffer-pool scale values, unique IDs, no blank observation/verification fields, and zero unexplained source records.

- [ ] **Step 4: Scan workbook errors**

Run a fresh formula-error scan for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, and `#N/A`; expected matches: zero.

- [ ] **Step 5: Report the verified totals and final artifact path**

Only claim completion after the verification script exits zero and reports the reconciled row counts.


# Factor Planning Subagent Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable prompt contract so clean-context subagents produce factor-association plans instead of generic SQL test plans.

**Architecture:** Add one human-readable mainflow reference that defines the required reasoning structure, then add a small Python CLI that resolves a statement key to repository references and prints a self-contained subagent prompt. Tests lock the prompt contract for `insert`.

**Tech Stack:** Python standard library, pytest, existing markdown/yaml reference files.

---

### Task 1: Contract Reference

**Files:**
- Create: `skills/pg-sql-generation/references/mainflow/plan_factor_association_from_statement.md`

- [ ] Write the reference with required output sections: impact chain, factor dimensions, trigger rules, association graph, oracle expectations, source attribution.

### Task 2: Prompt Builder CLI

**Files:**
- Create: `tools/build_factor_planning_prompt.py`
- Test: `tests/test_build_factor_planning_prompt.py`

- [ ] Write failing tests that call `build_prompt(root, "insert")`.
- [ ] Implement repository path resolution for statement references and matching combination matrices.
- [ ] Emit a prompt that tells a clean-context subagent not to create SQL or edit files.
- [ ] Include contract, statement, matrix, common policy, inventory, and type catalog paths.

### Task 3: Documentation And Verification

**Files:**
- Modify: `README.md`

- [ ] Add a short README pointer for factor-association subagent planning.
- [ ] Run targeted prompt-builder tests.
- [ ] Run the full pytest suite and matrix/catalog audits.
- [ ] Commit and push only files changed for this feature.

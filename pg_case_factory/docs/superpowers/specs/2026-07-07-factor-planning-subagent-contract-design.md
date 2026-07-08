# Factor Planning Subagent Contract Design

## Goal

Make clean-context subagents produce factor-association plans instead of ordinary SQL test summaries.

## Problem

When a subagent is asked to "plan INSERT coverage" without this conversation's context, it can read the repository and produce a useful expert checklist. That is not enough for this project. The desired output must explain the statement through an impact chain, enumerate factor dimensions, connect factors through trigger rules, and include an auditable association graph that can later drive SQL generation.

## Design

Add a reusable mainflow reference under `skills/pg-sql-generation/references/mainflow/` that defines the factor-association planning contract. The contract requires every subagent to output:

- an impact chain from syntax form to observable result,
- prioritized factor dimensions and values,
- factor-to-factor trigger rules,
- oracle and verification expectations,
- source attribution for catalog facts versus derived extensions,
- a YAML association graph.

Add a prompt-builder CLI under `tools/` that reads the statement reference and matching combination matrix, then emits a self-contained prompt for a clean-context subagent. The prompt includes the contract path, required repository files, and the exact output sections expected from the subagent.

## Scope

This change does not generate SQL and does not modify the existing combination matrices. It only standardizes the planning handoff so future agents can produce the richer reasoning format for `INSERT` and other statements.

## Verification

Tests must verify that the CLI prompt for `insert` includes the contract, the statement reference, the combination matrix, the impact-chain requirement, trigger-rule requirement, source attribution requirement, and YAML graph requirement.

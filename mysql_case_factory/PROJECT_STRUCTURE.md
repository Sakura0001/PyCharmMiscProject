# Project Structure

`mysql_case_factory` is a sibling of `pg_case_factory` in the shared monorepo.
The Python control plane is shared by both MySQL editions; every knowledge
asset is edition-local.

```text
mysql_case_factory/
├─ README.md
├─ PROJECT_STRUCTURE.md
├─ pyproject.toml
├─ docker-compose.smoke.yml
├─ docs/
│  ├─ migration/
│  └─ superpowers/
├─ editions/
│  ├─ mysql_8_0_22/
│  │  ├─ edition.yaml
│  │  └─ skills/mysql-8-0-22-sql-generation/
│  └─ mysql_8_0_41/
│     ├─ edition.yaml
│     ├─ version_delta_from_8_0_22.tsv
│     └─ skills/mysql-8-0-41-sql-generation/
├─ src/mysql_case_factory/
├─ tests/
└─ tools/
```

## Edition contract

`edition.yaml` is the trust root for an edition. It pins the exact MySQL patch,
skill root, statement-support inventory, factor-value ledger, and their
SHA-256 digests. The 8.0.41 manifest additionally pins the complete delta from
8.0.22. Loading an edition verifies paths stay inside the repository and all
declared files still match their digests.

The skill references are the source of truth for SQL semantics. Python code
must not hard-code a statement-specific lifecycle or factor list. Generated
inventories and matrices are reproducible from those references and are
audited before packaging.

## Control plane

`src/mysql_case_factory/` contains strict data contracts, canonical scope
inventories, plan expansion, applicability reconciliation, artifact storage,
job orchestration, SQL safety and deterministic-output audits, immutable
formal-run sealing, skill packaging, and exact-patch differential execution.

The basic runner permits SQL-only cases and rejects MySQL client commands,
server file access, plugin/component administration, topology changes, and
server lifecycle operations. Those capabilities require an explicit
`external_isolated` execution profile and named harness.

## Historical migration material

`docs/migration/` records the initial 8.0.22 migration review and official
source boundary. These files are provenance, not live runtime input. Current
edition completeness is determined by the edition-local inventories and
audits.

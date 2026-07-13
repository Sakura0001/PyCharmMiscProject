from __future__ import annotations

from pathlib import Path

import yaml

from mysql_case_factory.matrix_generation import generate_matrix_for_reference, load_statement_reference


def write_reference(root: Path) -> Path:
    path = root / "references" / "statements" / "ddl" / "table" / "create_example.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        """# CREATE EXAMPLE

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  statement: {key: create_example, name: CREATE EXAMPLE}
  factor_layers:
    - {tier: T1, factors: [mode, expected_status]}
    - {tier: T2, factors: [option]}
  factors:
    mode: {values: [one, two]}
    expected_status: {values: [success, failure]}
    option: {values: [omitted, present]}
  defaults: {mode: one, expected_status: success, option: omitted}
  coverage_policy:
    main_combination_axes: [mode, expected_status]
    non_main_factors: [option]
  rendering:
    statement_template: CREATE EXAMPLE {name}
    factor_value_bindings: {}
```
""",
        encoding="utf-8",
    )
    return path


def test_generation_expands_main_cartesian_and_every_non_main_value(tmp_path: Path) -> None:
    reference = write_reference(tmp_path)
    config = load_statement_reference(reference)
    matrix = generate_matrix_for_reference(reference, config, skill_root=tmp_path)

    groups = matrix["combination_groups"]
    main = [group for group in groups if not group["id"].startswith("supplemental__")]
    supplemental = [group for group in groups if group["id"].startswith("supplemental__")]
    assert len(main) == 4
    assert {group["factors"]["option"] for group in supplemental} == {"omitted", "present"}
    assert matrix["statement"]["source_reference"] == "references/statements/ddl/table/create_example.md"


def test_generated_matrix_is_yaml_round_trip_safe(tmp_path: Path) -> None:
    reference = write_reference(tmp_path)
    matrix = generate_matrix_for_reference(
        reference,
        load_statement_reference(reference),
        skill_root=tmp_path,
    )
    assert yaml.safe_load(yaml.safe_dump(matrix, sort_keys=False)) == matrix


def test_generation_rejects_reference_without_factors(tmp_path: Path) -> None:
    reference = write_reference(tmp_path)
    text = reference.read_text(encoding="utf-8").replace(
        "  factors:\n    mode: {values: [one, two]}\n    expected_status: {values: [success, failure]}\n    option: {values: [omitted, present]}\n",
        "  factors: {}\n",
    )
    reference.write_text(text, encoding="utf-8")
    config = load_statement_reference(reference)
    try:
        generate_matrix_for_reference(reference, config, skill_root=tmp_path)
    except ValueError as exc:
        assert "factors" in str(exc)
    else:
        raise AssertionError("factorless statement was accepted")

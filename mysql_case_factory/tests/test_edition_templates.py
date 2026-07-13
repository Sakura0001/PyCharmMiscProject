from __future__ import annotations

from pathlib import Path

import yaml

from mysql_case_factory.contracts import (
    load_coverage_plan,
    load_execution_profile,
    load_feature_manifest,
)
from mysql_case_factory.coverage import expand_coverage_plan, reconcile_obligations


ROOT = Path(__file__).resolve().parents[1]


def test_each_edition_ships_valid_complete_templates(tmp_path: Path) -> None:
    for directory, target in (
        ("mysql_8_0_22", "mysql-community-8.0.22"),
        ("mysql_8_0_41", "mysql-community-8.0.41"),
    ):
        edition = ROOT / "editions" / directory
        manifest = yaml.safe_load((edition / "edition.yaml").read_text(encoding="utf-8"))
        skill = edition / manifest["skill"]["root"]
        templates = skill / "assets" / "templates"
        source = tmp_path / f"{directory}.md"
        source.write_text("# Feature\n", encoding="utf-8")
        feature_document = yaml.safe_load((templates / "feature_manifest_template.yaml").read_text(encoding="utf-8"))
        import hashlib

        feature_document["source"]["path"] = source.name
        feature_document["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        feature_path = tmp_path / f"{directory}-feature.yaml"
        feature_path.write_text(yaml.safe_dump(feature_document, sort_keys=False), encoding="utf-8")
        loaded_manifest = load_feature_manifest(feature_path, verify_source=True)
        assert loaded_manifest.compatibility_target == target

        plan = load_coverage_plan(
            templates / "coverage_plan_template.yaml",
            manifest=loaded_manifest,
            inventory_root=skill,
        )
        obligations = expand_coverage_plan(plan, require_complete=True)
        assert reconcile_obligations(obligations).complete is True
        assert obligations

        profile = load_execution_profile(templates / "execution_profile_template.yaml")
        assert profile.compatibility_target == target

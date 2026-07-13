from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_docker_smoke_compose_pins_two_distinct_endpoints_per_edition() -> None:
    document = yaml.safe_load((ROOT / "docker-compose.smoke.yml").read_text())
    services = document["services"]
    assert set(services) == {
        "mysql8022-reference",
        "mysql8022-candidate",
        "mysql8041-reference",
        "mysql8041-candidate",
    }
    assert [services[name]["image"] for name in services].count("mysql:8.0.22") == 2
    assert [services[name]["image"] for name in services].count("mysql:8.0.41") == 2
    assert len({tuple(services[name]["ports"]) for name in services}) == 4

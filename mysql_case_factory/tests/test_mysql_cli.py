from __future__ import annotations

from pathlib import Path

from mysql_case_factory.cli import main, main_8022, main_8041


ROOT = Path(__file__).resolve().parents[1]


def test_generic_cli_requires_an_explicit_edition(capsys) -> None:
    assert main(["doctor", "--root", str(ROOT)]) == 2
    assert "--edition" in capsys.readouterr().err


def test_generic_cli_doctor_accepts_each_edition(capsys) -> None:
    assert main(["--edition", "8.0.22", "doctor", "--root", str(ROOT)]) == 0
    assert "mysql-community-8.0.22" in capsys.readouterr().out
    assert main(["--edition", "8.0.41", "doctor", "--root", str(ROOT)]) == 0
    assert "mysql-community-8.0.41" in capsys.readouterr().out


def test_dedicated_entry_points_inject_their_exact_edition(capsys) -> None:
    assert main_8022(["doctor", "--root", str(ROOT)]) == 0
    assert "mysql-community-8.0.22" in capsys.readouterr().out
    assert main_8041(["doctor", "--root", str(ROOT)]) == 0
    assert "mysql-community-8.0.41" in capsys.readouterr().out


def test_dedicated_entry_point_rejects_conflicting_edition(capsys) -> None:
    assert main_8022(["--edition", "8.0.41", "doctor", "--root", str(ROOT)]) == 2
    assert "conflicts" in capsys.readouterr().err


def test_help_lists_parity_command_groups(capsys) -> None:
    assert main(["--help"]) == 0
    output = capsys.readouterr().out
    for command in ("doctor", "applicability", "plan", "run", "skill"):
        assert command in output
